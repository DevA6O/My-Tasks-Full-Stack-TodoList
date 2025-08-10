import os
import jwt
import json
import uuid
import time
import pytest
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from http.cookies import SimpleCookie
from fastapi.responses import JSONResponse

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Callable, Optional, Union

from database.models import User
from database.connection import get_db
from main import api
from security.jwt import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, REFRESH_MAX_AGE,
    get_bearer_token, decode_token, create_token, set_refresh_token
)


class TestGetBearerToken:
    """ Test class for different test scenarios for the get_bearer_token function """
    
    def test_get_bearer_token_success(self) -> None:
        """ Tests the success case """
        token: str = create_token(data={"sub": str(uuid.uuid4())})
        header: str = f"Bearer {token}"

        result = get_bearer_token(authorization=header)
        assert result == token
        
    def test_get_bearer_token_failed_because_no_token(self) -> None:
        """ Tests the error case when there is no token in the header """
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_bearer_token(authorization="")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail


class TestDecodeToken:
    """ Test class for different test scenarios for the decode_token function """

    def test_decode_token_success(self) -> None:
        """ Tests the success case """
        user_id: uuid.UUID = uuid.uuid4()
        token: str = create_token(data={"sub": str(user_id)})
        
        result = decode_token(token=token)
        assert result == user_id

    def test_decode_token_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        token: str = create_token(data={"no_sub": str(uuid.uuid4())})
        
        with pytest.raises(ValueError):
            decode_token(token=token)

    def test_decode_token_failed_because_py_jwt_error(self) -> None:
        """ Tests the failed case when a PyJWTError occurrs """
        token: str = create_token(data={"sub": str(uuid.uuid4())}, expire_delta=timedelta(seconds=1))
        time.sleep(1.5) # Wait until the token is expired (invalid)

        result = decode_token(token=token)
        assert result is None


class TestCreateToken:
    """ Test class for different test scenarios for the create_token function """

    @pytest.mark.parametrize("minutes", [(ACCESS_TOKEN_EXPIRE_MINUTES), (5)])
    def test_create_token_success(self, minutes: int) -> None:
        """ Tests the success case when an expiration date is set and when it is not """
        if minutes == ACCESS_TOKEN_EXPIRE_MINUTES:
            token: str = create_token(data={"sub": str(uuid.uuid4())})
        else:
            token: str = create_token(data={"sub": str(uuid.uuid4())}, expire_delta=timedelta(minutes=minutes))
        assert isinstance(token, str)

        # Tests the expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        # Allows a deviation of 2 seconds
        assert abs((exp_datetime - expected_exp).total_seconds()) < 2

    @pytest.mark.parametrize("data", [(None, str("Not a dict"))])
    def test_create_token_failed_because_data_is_set_incorrect(self, data: str | None) -> None:
        """ Tests the failed case when the data is set incorrectly """
        with pytest.raises(ValueError):
            create_token(data=data)

    def test_create_token_failed_because_expire_delta_is_set_incorrect(self) -> None:
        """ Tests the failed case when expire_delta is set incorrectly """
        with pytest.raises(ValueError):
            create_token(data={"sub": str(uuid.uuid4())}, expire_delta=False)


class TestSetRefreshToken:
    """ Test class for different test scenarios for the set_refresh_token function """

    @pytest.mark.parametrize("secure_https", [(True), (False), (None)])
    def test_set_refresh_token_success(self, secure_https: bool, monkeypatch) -> None:
        """ Tests the success case """
        # Manipulate the .env variable SECURE_HTTPS
        if secure_https:
            monkeypatch.setenv("SECURE_HTTPS", str(secure_https).lower())
        elif secure_https is None or not secure_https:
            monkeypatch.delenv("SECURE_HTTPS", raising=False)

        # Sets the refresh token
        response: JSONResponse = set_refresh_token(user_id=uuid.uuid4())
        assert response.status_code == 200

        # Checks whether the cookie is set correctly
        cookie = response.headers["set-cookie"]

        assert "set-cookie" in response.headers
        assert "refresh_token" in cookie
        assert "HttpOnly" in cookie
        assert "Path=/" in cookie
        assert "SameSite=lax" in cookie
        assert f"Max-Age={REFRESH_MAX_AGE}" in cookie
        
        if secure_https:
            assert "Secure" in cookie
        else:
            assert "Secure" not in cookie


    def test_set_refresh_token_success_but_only_test_param_values(self) -> None:
        """ Tests the success case but it will only check whether 
        the function params are set correctly """
        user_id: uuid.UUID = uuid.uuid4()
        status_code: int = 510 # Intenionally use an unusual status code
        content: dict = {"message": "Successfully added: Refresh token successfully added."}

        response: JSONResponse = set_refresh_token(user_id=user_id, status_code=status_code, content=content)
        assert response.status_code == status_code
        assert json.loads(response.body.decode("utf-8")) == content

        # Gets the refresh token and decodes the token
        for part in response.headers["set-cookie"].split(";"):
            if part.strip().startswith("refresh_token="):
                refresh_token: str = part.strip().split("=", 1)[1]

                decoded_user_id = decode_token(token=refresh_token)
        
        assert decoded_user_id == user_id


    @pytest.mark.parametrize(
        "valid_user_id, valid_status_code, valid_content",
        [
            (False, True, True),
            (True, False, True),
            (True, True, False)
        ]
    )
    def test_refresh_token_failed_because_invalid_param_types(
        self, valid_user_id: bool, valid_status_code: bool, valid_content: bool
    ) -> None:
        """ Tests the failed case when one of the params in the function 
        has the wrong type """
        user_id: uuid.UUID = uuid.uuid4()
        status_code: int = 200
        content: dict = {}

        if not valid_user_id:
            user_id = int(0)

        elif not valid_status_code:
            status_code = str("Invalid status_code")

        elif not valid_content:
            content = str("Not a dict")

        with pytest.raises(ValueError):
            set_refresh_token(user_id=user_id, status_code=status_code, content=content)




# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "user_id, status_code, content, secure_https, expected_secure_flag, expected_exception",
#     [
#         (uuid.uuid4(), 200, {}, "true", True, None), # Success
#         (uuid.uuid4(), 200, {}, "false", False, None), # Success with secure=False
#         (uuid.uuid4(), 200, None, "true", True, None), # Success with empty content
#         (uuid.uuid4(), 200, {}, None, False, None), # Success with secure=None -> defaults to False (Fallback)
#         (uuid.uuid4(), 200, "NotADict", "true", True, ValueError), # Invalid content -> ValueError
#         (uuid.uuid4(), "NotAnInteger", {}, "true", True, ValueError), # Invalid status_code -> ValueError
#         ("NotAUUID", 200, {}, "true", True, ValueError), # Invalid user_id -> ValueError
#     ]
# )
# async def test_set_refresh_token(
#     monkeypatch, user_id: uuid.UUID, status_code: int, content: dict, 
#     secure_https: str, expected_secure_flag: bool, expected_exception: Optional[Exception]
# ) -> None:
#     # If an exception is expected
#     if expected_exception:
#         with pytest.raises(expected_exception):
#             await set_refresh_token(user_id=user_id, status_code=status_code, content=content)
#         return
    
#     # If no exception is expected

#     # Set the env variable for secure HTTPS
#     if secure_https is not None:
#         monkeypatch.setenv("SECURE_HTTPS", secure_https)
#     else:
#         monkeypatch.delenv("SECURE_HTTPS", raising=False)

#     response: JSONResponse = await set_refresh_token(user_id=user_id, status_code=status_code, content=content)

#     # Check response content and status
#     assert response.status_code == status_code
    
#     parsed_content = json.loads(response.body.decode())
#     assert parsed_content == content

#     # Check cookie
#     cookie = SimpleCookie()
#     cookie.load(response.headers.get("set-cookie"))
#     refresh_cookie = cookie.get("refresh_token")
#     refresh_token = refresh_cookie.value
    
#     # Decode the JWT token
#     payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
#     assert payload["sub"] == str(user_id)
    
#     # Cookie attributes
#     assert refresh_cookie["httponly"]
#     assert refresh_cookie["samesite"].lower() == "lax"
#     assert refresh_cookie["path"] == "/"
#     assert int(refresh_cookie["max-age"]) == REFRESH_MAX_AGE

#     if expected_secure_flag:
#         assert refresh_cookie["secure"] == True or refresh_cookie["secure"] == "True"
#     else:
#         assert refresh_cookie["secure"] in (False, "", None, "False")





# def _generate_refresh_token(token_validity: str, user_id: uuid.UUID) -> Optional[str]:
#     """ Helper function for the test function refresh_token """
#     token_generators: dict[str, Callable[[], Optional[str]]] = {
#         "missing": lambda: None,
#         "invalid_format": lambda: "not.a.jwt",
#         "wrong_signature": lambda: jwt.encode(
#             {"sub": str(user_id)},
#             "WRONG_SECRET",
#             algorithm=ALGORITHM
#         ),
#         "expired": lambda: jwt.encode(
#             {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
#             SECRET_KEY,
#             algorithm=ALGORITHM
#         ),
#         "valid": lambda: jwt.encode(
#             {"sub": str(user_id), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
#             SECRET_KEY,
#             algorithm=ALGORITHM
#         ),
#     }

#     try:
#         return token_generators[token_validity]()
#     except KeyError as e:
#         raise KeyError(f"Unknown token state: {e}")

# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "user_in_db, token_validity, user_id_valid, expected_status_code",
#     [
#         (True, "valid", True, 200), # Success
#         (True, "missing", True, 401), # No token
#         (True, "invalid_format", True, 401), # Invalid token
#         (True, "wrong_signature", True, 401), # Invalid signature
#         (True, "expired", True, 401), # Invalid token (due to expire date)
#         (True, "valid", False, 401), # user_id does not exist
#         (False, "valid", True, 401), # user is not in the db
#     ]
# )
# async def test_refresh_token(
#     user_in_db: bool, token_validity: str, user_id_valid: True, 
#     expected_status_code: str, fake_user: Tuple[User, AsyncSession]
# ) -> None:
#     # Define the fake informations
#     user, db_session = fake_user

#     # Define user_id
#     if user_id_valid:
#         user_id = user.id
#     else:
#         user_id = uuid.uuid4() # Fake user with no db entry

#     if not user_in_db: # Deletes the fake user for the test case
#         stmt = delete(User).where(User.id == user.id)
#         await db_session.execute(stmt)

#     # Create token
#     refresh_token = _generate_refresh_token(token_validity=token_validity, user_id=user_id)
#     cookies = {"refresh_token": refresh_token} if refresh_token else {}

#     # Start test
#     api.dependency_overrides[get_db] = lambda: db_session
#     transport = ASGITransport(app=api)

#     async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL"), cookies=cookies) as ac:
#         response = await ac.post("/refresh")

#     assert response.status_code == expected_status_code
#     api.dependency_overrides.clear()