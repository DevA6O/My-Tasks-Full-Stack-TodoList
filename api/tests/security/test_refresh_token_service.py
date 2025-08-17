import jwt
import json
import uuid
import time
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
from typing import Tuple

from database.models import User, Auth
from security.refresh_token_service import (
    RefreshTokenService, is_refresh_token_valid,
    REFRESH_MAX_AGE, SECRET_KEY, ALGORITHM
)


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

                payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
                decoded_user_id = payload.get("sub")
        
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



class TestIsRefreshTokenValidFunction:
    """ Test class for different test scenarios for is_refresh_token_valid function """

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
    async def test_is_refresh_token_valid_success(self) -> None:
        """ Tests the success case """
        # Insert a token in database
        refresh_token = await self.service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Check whether the inserted token is valid
        result = await is_refresh_token_valid(user_id=self.user.id, db_session=self.db_session)
        assert result

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_failed_because_no_token_in_db(self) -> None:
        """ Tests the failed case when no token is in the database """
        result = await is_refresh_token_valid(user_id=self.user.id, db_session=self.db_session)
        assert not result

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_failed_because_token_is_revoked(self) -> None:
        """ Tests the failed case when the token is revoked """
        # Create a token
        refresh_token = await self.service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Set token to revoked
        stmt = update(Auth).where(Auth.user_id == self.user.id).values(
            revoked=True
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()

        # Start the test
        result = await is_refresh_token_valid(user_id=self.user.id, db_session=self.db_session)
        assert not result

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_failed_because_token_is_expired(self) -> None:
        """ Tests the failed case when the token is expired """
        # Create a token
        refresh_token = await self.service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Set token expiration to expired
        stmt = update(Auth).where(Auth.user_id == self.user.id).values(
            expires_at=int(datetime.now(timezone.utc).timestamp())
        )
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()

        time.sleep(1) # <- Safety buffer

        # Start the test
        result = await is_refresh_token_valid(user_id=self.user.id, db_session=self.db_session)
        assert not result

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_failed_because_db_is_broken(self) -> None:
        """ Tests the failed case when the database is broken """
        # Create a token (So that it doesn't fail because of that)
        refresh_token = await self.service._create_and_store_refresh_token()
        assert isinstance(refresh_token, str)

        # Mock the database session
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken database session")

        # Start the test
        result = await is_refresh_token_valid(user_id=self.user.id, db_session=broken_session)
        assert not result