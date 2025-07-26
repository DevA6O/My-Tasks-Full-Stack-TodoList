import os
import jwt
import json
import uuid
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from http.cookies import SimpleCookie
from fastapi.responses import JSONResponse

from sqlalchemy import insert, delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Callable, Optional

from database.models import User
from database.connection import get_db
from main import api
from security.jwt import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_MAX_AGE,
    create_token, set_refresh_token
)

@pytest.mark.parametrize(
    "data, expire_delta, expected_exception",
    [
        ({"sub": str(uuid.uuid4())}, None, None), # Success case with default expiration
        ({"sub": str(uuid.uuid4())}, timedelta(minutes=10), None), # Success
        ({}, None, ValueError), # Empty data -> ValueError
        ("NotADict", None, ValueError), # Non-dict -> ValueError
        ({"sub": str(uuid.uuid4())}, "NotATimedeltaOrNone", ValueError), # Non-timedelta or None -> ValueError
    ]
)
def test_create_token(data: dict, expire_delta: timedelta, expected_exception: Exception) -> None:
    # If an exception is expected
    if expected_exception:
        with pytest.raises(expected_exception):
            create_token(data=data, expire_delta=expire_delta)
        return
    
    # If no exception is expected
    token = create_token(data=data)
    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Test whether the data is correct set
    assert decoded_token["sub"] == data["sub"]
    assert "exp" in decoded_token

    # Check that the expiry date is correct.
    expire = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
    assert expire > datetime.now(timezone.utc)

    # Check that the expiry date is within the expected range
    now = datetime.now(timezone.utc)
    delta = expire - now

    assert 0 < delta.total_seconds() <= ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, status_code, content, secure_https, expected_secure_flag, expected_exception",
    [
        (uuid.uuid4(), 200, {}, "true", True, None), # Success
        (uuid.uuid4(), 200, {}, "false", False, None), # Success with secure=False
        (uuid.uuid4(), 200, {}, None, False, None), # Success with secure=None -> defaults to False (Fallback)
        (uuid.uuid4(), 200, "NotADict", "true", True, ValueError), # Invalid content -> ValueError
        (uuid.uuid4(), "NotAnInteger", {}, "true", True, ValueError), # Invalid status_code -> ValueError
        ("NotAUUID", 200, {}, "true", True, ValueError), # Invalid user_id -> ValueError
    ]
)
async def test_set_refresh_token(
    monkeypatch, user_id: uuid.UUID, status_code: int, content: dict, 
    secure_https: str, expected_secure_flag: bool, expected_exception: Optional[Exception]
) -> None:
    # If an exception is expected
    if expected_exception:
        with pytest.raises(expected_exception):
            await set_refresh_token(user_id=user_id, status_code=status_code, content=content)
        return
    
    # If no exception is expected

    # Set the env variable for secure HTTPS
    if secure_https is not None:
        monkeypatch.setenv("SECURE_HTTPS", secure_https)
    else:
        monkeypatch.delenv("SECURE_HTTPS", raising=False)

    response: JSONResponse = await set_refresh_token(user_id=user_id, status_code=status_code, content=content)

    # Check response content and status
    assert response.status_code == status_code
    
    parsed_content = json.loads(response.body.decode())
    assert parsed_content == content

    # Check cookie
    cookie = SimpleCookie()
    cookie.load(response.headers.get("set-cookie"))
    refresh_cookie = cookie.get("refresh_token")
    refresh_token = refresh_cookie.value
    
    # Decode the JWT token
    payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(user_id)
    
    # Cookie attributes
    assert refresh_cookie["httponly"]
    assert refresh_cookie["samesite"].lower() == "lax"
    assert refresh_cookie["path"] == "/"
    assert int(refresh_cookie["max-age"]) == REFRESH_MAX_AGE

    if expected_secure_flag:
        assert refresh_cookie["secure"] == True or refresh_cookie["secure"] == "True"
    else:
        assert refresh_cookie["secure"] in (False, "", None, "False")





def _generate_refresh_token(token_validity: str, user_id: uuid.UUID) -> Optional[str]:
    """ Helper function for the test function refresh_token """
    token_generators: dict[str, Callable[[], Optional[str]]] = {
        "missing": lambda: None,
        "invalid_format": lambda: "not.a.jwt",
        "wrong_signature": lambda: jwt.encode(
            {"sub": str(user_id)},
            "WRONG_SECRET",
            algorithm=ALGORITHM
        ),
        "expired": lambda: jwt.encode(
            {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            SECRET_KEY,
            algorithm=ALGORITHM
        ),
        "valid": lambda: jwt.encode(
            {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            SECRET_KEY,
            algorithm=ALGORITHM
        ),
    }

    try:
        return token_generators[token_validity]()
    except KeyError as e:
        raise KeyError(f"Unknown token state: {e}")

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_in_db, token_validity, user_id_valid, expected_status_code",
    [
        (True, "valid", True, 200), # Success
        (True, "missing", True, 401), # No token
        (True, "invalid_format", True, 401), # Invalid token
        (True, "wrong_signature", True, 401), # Invalid signature
        (True, "expired", True, 401), # Invalid token (due to expire date)
        (True, "valid", False, 401), # user_id does not exist
        (False, "valid", True, 401), # user is not in the db
    ]
)
async def test_refresh_token(
    user_in_db: bool, token_validity: str, user_id_valid: True, 
    expected_status_code: str, fake_user: Tuple[User, AsyncSession]
) -> None:
    # Define the fake informations
    user, db_session = fake_user

    # Define user_id
    if user_id_valid:
        user_id = user.id
    else:
        user_id = uuid.uuid4() # Fake user with no db entry

    if not user_in_db: # Deletes the fake user for the test case
        stmt = delete(User).where(User.id == user.id)
        await db_session.execute(stmt)

    # Create token
    refresh_token = _generate_refresh_token(token_validity=token_validity, user_id=user_id)
    cookies = {"refresh_token": refresh_token} if refresh_token else {}

    # Start test
    api.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=api)

    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL"), cookies=cookies) as ac:
        response = await ac.post("/refresh")

    assert response.status_code == expected_status_code
    api.dependency_overrides.clear()