import os
import json
import uuid
import time
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
from typing import Tuple

from database.connection import get_db
from database.models import User, Auth
from security.jwt import create_token, decode_token
from security.refresh_token_service import (
    RefreshTokenService, RefreshTokenVerifier,
    REFRESH_MAX_AGE
)
from main import api

load_dotenv()

class TestCreateAndStoreRefreshTokenMethod:
    """ Test class for different test scenarios for _create_and_store_refresh_token method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user
        
        # Define test values
        self.user_agent_str = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) " \
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {"user-agent": self.user_agent_str}
        self.mock_request.client.host = "123.123.123.123"

        self.service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id,
            db_session=self.db_session, status_code=200, content={}
        )

    @pytest.mark.asyncio
    async def test_create_and_store_refresh_token_success(self) -> None:
        """ Tests the success case """
        refresh_token = await self.service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Check whether the data is stored correctly
        expires_at = (datetime.now(timezone.utc) + timedelta(seconds=REFRESH_MAX_AGE)).timestamp()

        stmt = select(Auth).where(Auth.user_id == self.user.id)
        result = await self.db_session.execute(stmt)
        auth_obj = result.scalar_one_or_none()

        assert auth_obj is not None
        assert abs(auth_obj.expires_at - expires_at) <= 5 # May have a difference of 5 seconds

    @pytest.mark.asyncio
    async def test_create_and_store_refresh_token_failed_because_storage_failed(self) -> None:
        """ Tests the failed case when the storage failed """
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(self.db_session, "execute", new=AsyncMock(return_value=mock_result)):
            refresh_token = await self.service._create_and_store_refresh_token()
            assert not refresh_token


class TestSetRefreshTokenMethod:
    """ Test class for different test scenarios for set_refresh_token method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define test values
        self.user_agent_str = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) " \
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {"user-agent": self.user_agent_str}
        self.mock_request.client.host = "123.123.123.123"

        self.service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id,
            db_session=self.db_session, status_code=200, content={}
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize("secure_https", [(True), (False), (None)])
    async def test_set_refresh_token_success(self, secure_https: bool) -> None:
        """ Tests the success case """
        patch_value = True if secure_https else False

        with patch("security.refresh_token_service.SECURE_HTTPS", patch_value):
            # Sets the refresh token
            response: JSONResponse = await self.service.set_refresh_token()
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


    @pytest.mark.asyncio
    async def test_set_refresh_token_sets_correct_response_and_token_data(self) -> None:
        """ Tests that the refresh token is set correctly in the response 
        and that the token contains the correct user_id """
        response: JSONResponse = await self.service.set_refresh_token()
        assert response.status_code == self.service.status_code
        assert json.loads(response.body.decode("utf-8")) == self.service.content

        # Gets the refresh token and decodes the token
        for part in response.headers["set-cookie"].split(";"):
            if part.strip().startswith("refresh_token="):
                refresh_token: str = part.strip().split("=", 1)[1]

                payload: dict = decode_token(token=refresh_token)
                decoded_user_id: str = payload.get("sub")
        
        assert uuid.UUID(decoded_user_id) == self.service.user_id


    @pytest.mark.asyncio
    async def test_set_refresh_token_failed_because_http_exception_raised(self) -> None:
        """ Tests the failed case when the storage failed and a http exception 
        raised """
        with patch(
            "security.refresh_token_service.RefreshTokenService._create_and_store_refresh_token", 
            new=AsyncMock(return_value=False)
        ):
            with pytest.raises(HTTPException):
                await self.service.set_refresh_token()


class TestGetRefreshTokenMethod:
    """ Test class for different test scenarios for _get_refresh_token method """

    @pytest.fixture(autouse=True)
    def setup(self, db_session: AsyncSession) -> None:
        """ Set up common test data """
        self.db_session: AsyncSession = db_session

        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.client.host = "123.123.123.123"

        self.token = create_token(data={
            "sub": str(uuid.uuid4()), 
            "jti": str(uuid.uuid4())
        })
        self.mock_request.cookies = {"refresh_token": self.token}
        
    def test_get_refresh_token_success(self) -> None:
        """ Tests the success case """
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)
        result = verifier._get_refresh_token()
        assert isinstance(result, str)

    def test_get_refresh_token_failed_because_no_refresh_token(self) -> None:
        """ Tests the failed case when no refresh token is given """
        mock_request = self.mock_request
        mock_request.cookies = {}

        verifier = RefreshTokenVerifier(request=mock_request, db_session=self.db_session)

        with pytest.raises(HTTPException) as exc_info:
            verifier._get_refresh_token()
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail


class TestCheckTokenInDb:
    """ Test class for different test scenarios for _check_token_in_db method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Mock request
        self.user_agent_str = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) " \
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {"user-agent": self.user_agent_str}
        self.mock_request.client.host = "000.000.000.000"

    @pytest.mark.asyncio
    async def test_check_token_in_db_success(self) -> None:
        """ Tests the success case """
        # Create and save refresh token
        service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id,
            db_session=self.db_session
        )
        refresh_token: str = await service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Get the jti id
        payload: dict = decode_token(token=refresh_token)
        jti_id: str = payload.get("jti")

        # Start the test
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)
        auth_obj: Auth = await verifier._check_token_in_db(user_id=self.user.id, jti_id=uuid.UUID(jti_id))
        assert isinstance(auth_obj, Auth)

    @pytest.mark.asyncio
    async def test_check_token_in_db_failed_because_no_token_in_db(self) -> None:
        """ Tests the failed case when no token is in the database """
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)
        auth_obj: None = await verifier._check_token_in_db(user_id=self.user.id, jti_id=uuid.uuid4())
        assert auth_obj is None

    @pytest.mark.asyncio
    async def test_check_token_in_db_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)
        
        with pytest.raises(ValueError):
            await verifier._check_token_in_db(user_id=self.user.id, jti_id="No an UUID.")
        

class TestIsValidMethod:
    """ Test class for different test scenarios for is_valid method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Mock request
        self.user_agent_str = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) " \
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {"user-agent": self.user_agent_str}
        self.mock_request.client.host = "000.000.000.000"


    @pytest.mark.asyncio
    async def test_is_valid_success(self) -> None:
        """ Tests the success case """
        # Create and save refresh token
        service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id,
            db_session=self.db_session
        )
        refresh_token: str = await service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Mock cookies in request
        self.mock_request.cookies = {"refresh_token": refresh_token}

        # Start the test
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)
        auth_obj: Auth = await verifier.is_valid()
        assert isinstance(auth_obj, Auth)


    @pytest.mark.asyncio
    @pytest.mark.parametrize("user_id, jti_id", [(True, False), (False, True)])
    async def test_is_valid_failed_because_no_user_or_no_jti(self, user_id: bool, jti_id: bool) -> None:
        """ Tests the failed case when no user_id or not jti_id is in the payload """
        # Create a refresh token
        if user_id:
            refresh_token = create_token(data={"sub": str(self.user.id)})
        elif jti_id:
            refresh_token = create_token(data={"jti": str(uuid.uuid4())})

        self.mock_request.cookies = {"refresh_token": refresh_token}

        # Start the test
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)

        with pytest.raises(HTTPException) as exc_info:
            await verifier.is_valid()
       
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization failed: Invalid token structure."

    
    @pytest.mark.asyncio
    async def test_is_valid_failed_because_token_is_not_in_db(self) -> None:
        """ Tests the failed case when the token is not in the database """
        refresh_token = create_token(data={"sub": str(self.user.id), "jti": str(uuid.uuid4())})
        self.mock_request.cookies = {"refresh_token": refresh_token}

        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=self.db_session)

        with pytest.raises(HTTPException) as exc_info:
            await verifier.is_valid()

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization failed: Authentication token could not be found."

    
    @pytest.mark.asyncio
    async def test_is_valid_failed_because_db_error(self) -> None:
        """ Tests the failed case when a database error occurrs """
        # Create token
        refresh_token = create_token(data={"sub": str(self.user.id), "jti": str(uuid.uuid4())})
        self.mock_request.cookies = {"refresh_token": refresh_token}

        # Mock database session
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken database session")
        
        # Start the test
        verifier = RefreshTokenVerifier(request=self.mock_request, db_session=broken_session)

        with pytest.raises(HTTPException) as exc_info:
            await verifier.is_valid()

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Authorization failed: An unknown error has occurred. Please try again later."


class TestIsRefreshTokenValidAPIEndpoint:
    """ Test class for different test scenarios for api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Set up the dependency
        api.dependency_overrides[get_db] = lambda: self.db_session

        self.base_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/token/refresh/valid"
        self.transport = ASGITransport(app=api)

        # Create refresh token
        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {}
        self.mock_request.client.host = "123.123.123.123"

        self.service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id,
            db_session=self.db_session, status_code=200, content={}
        )

        self.refresh_token = await self.service._create_and_store_refresh_token()
        self.cookies = {"refresh_token": self.refresh_token}

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_endpoint_success(self) -> None:
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
        """ Tests the failed case when the user is not in the refresh token """
        cookies = {"refresh_token": create_token(data={"no_sub": str(uuid.uuid4())})}

        async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=cookies) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 401
            assert "detail" in response.json()

    @pytest.mark.asyncio
    async def test_refresh_token_endpoint_failed_because_jti_does_not_exist(self) -> None:
        """ Tests the failed case when the jti id is not in the refresh token """
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
        with patch("security.refresh_token_service.RefreshTokenVerifier._check_token_in_db", side_effect=ValueError("Validation failed: ...")):
            async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
                response = await ac.post(self.path_url)
                assert response.status_code == 400
                assert "detail" in response.json()