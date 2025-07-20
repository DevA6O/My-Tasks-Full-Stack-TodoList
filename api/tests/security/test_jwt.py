import jwt
import os
import uuid
import pytest
import pytest_asyncio
from dotenv import load_dotenv
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
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, 
    create_token, set_refresh_token
)

load_dotenv()


def test_create_token() -> None:
    data: dict = {"sub": str(uuid.uuid4())}
    token = create_token(data=data)

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    
    # Test whether the data is correct set
    assert decoded_token["sub"] == data["sub"]
    assert "exp" in decoded_token

    # Check that the expiry date is correct.
    expire = datetime.fromtimestamp(decoded_token["exp"], tz=timezone.utc)
    assert expire > datetime.now(timezone.utc)

    now = datetime.now(timezone.utc)
    delta = expire - now

    assert 0 < delta.total_seconds() <= ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 5


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "secure_https, expected_secure_flag",
    [
        (True, True),   # Success: Only over HTTPS - Secure cookie is set
        (False, False), # Success: Dev/local mode - no Secure flag in cookie
        (None, False),  # Fallback: ENV var not set - default is Secure=False
    ]
)
async def test_set_refresh_token(
    monkeypatch, secure_https: bool, expected_secure_flag: Optional[bool]
) -> None:
    fake_user_id = uuid.uuid4()

    # Change the value in the .env file
    if secure_https is not None:
        monkeypatch.setenv("SECURE_HTTPS", str(secure_https))
    else:
        monkeypatch.delenv("SECURE_HTTPS", raising=False)
    
    # Get the response and parse the set-cookie header using http.cookie for correctness
    response: JSONResponse = await set_refresh_token(fake_user_id)
    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None

    # Parse the Set-Cookie header to extract the refresh_token value
    cookie = SimpleCookie()
    cookie.load(set_cookie)
    assert "refresh_token" in cookie # Ensure the cookie was set
    token_value = cookie["refresh_token"].value # Extract the JWT token from the cookie

    # Decode the refresh token
    payload = jwt.decode(token_value, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == str(fake_user_id)

    # Validate the refresh token
    refresh_cookie = cookie["refresh_token"]
    assert refresh_cookie["httponly"]
    assert refresh_cookie["samesite"].lower() == "lax"
    assert refresh_cookie["path"] == "/"
    assert int(refresh_cookie["max-age"]) == 60 * 60 * 24 * 7

    # Checks whether the secure flag is correct
    if expected_secure_flag:
        assert refresh_cookie["secure"]
    else:
        assert "secure" not in refresh_cookie or not refresh_cookie["secure"]


@pytest_asyncio.fixture
async def fake_user(db_session: AsyncSession) -> Tuple[User, AsyncSession]:
    stmt = (
        insert(User)
        .values(name="fake_user", email="fake@email.com", password="very_secret_pwd")
        .returning(User)
    )
    result_obj = await db_session.execute(stmt)
    result = result_obj.scalar_one_or_none()
    assert result is not None
    return result, db_session



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