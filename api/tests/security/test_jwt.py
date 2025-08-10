import os
import jwt
import json
import uuid
import time
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from httpx import AsyncClient, ASGITransport
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

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



class TestRefreshTokenAPIEndpoint:
    """ Test class for different test scenarios for the api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Set up dependency
        api.dependency_overrides[get_db] = lambda: self.db_session

        self.transport = ASGITransport(app=api)
        self.base_url = os.getenv("VITE_API_URL")
        self.path_url = "/refresh"
        self.refresh_token = create_token(data={"sub": str(self.user.id)})
        self.cookies = {"refresh_token": self.refresh_token}

    def teardown_method(self) -> None:
        api.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_success(self) -> None:
        """ Tests the success case """
        async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 200
            assert "access_token" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_failed_because_refresh_token_does_not_exist(self) -> None:
        """ Tests the error case when the refresh token is not present 
        in the cookies """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 401
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_failed_because_user_does_not_exist(self) -> None:
        """ Tests the failed case when the user is no longer present 
        in the database """
        cookies = {"refresh_token": create_token(data={"sub": str(uuid.uuid4())})}

        async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=cookies) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 401
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_failed_because_py_jwt_error(self) -> None:
        """ Tests the failed case when a PyJWTError occurrs """
        cookies = {
            "refresh_token": create_token(
                data={"sub": str(self.user.id)},
                expire_delta=timedelta(seconds=1)
        )}
        time.sleep(1.5) # Wait until the token is invalid

        async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=cookies) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 401
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        from unittest.mock import patch

        with patch("security.jwt.create_token", side_effect=ValueError("Validation failed: ...")):
            async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
                response = await ac.post(self.path_url)
                assert response.status_code == 400
                assert "detail" in response.json()