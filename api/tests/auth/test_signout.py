import os
import pytest
import pytest_asyncio
from uuid import UUID
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, Mock, patch
from typing import Tuple

from security.jwt import decode_token
from security.refresh_token_service import RefreshTokenService
from database.connection import get_db
from database.models import User, Auth
from main import api

load_dotenv()

class TestSignoutAPIEnpoint:
    """ Test class for different test scenarios for the API endpoint """

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
        self.mock_request.client.host = "123.123.123.123"

        # Set dependency
        api.dependency_overrides[get_db] = lambda: self.db_session
        
        self.transport = ASGITransport(app=api)
        self.base_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/signout"

        self.refresh_service = RefreshTokenService(
            request=self.mock_request, user_id=self.user.id, db_session=self.db_session
        )
        self.refresh_token = await self.refresh_service._create_and_store_refresh_token()
        self.cookies = {"refresh_token": self.refresh_token}

    def teardown_method(self):
        api.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_signout_endpoint_success(self) -> None:
        """ Tests the success case """
        async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 200

        # Check whether the token is revoked in the database
        payload: dict = decode_token(token=self.refresh_token)
        jti_id: UUID = UUID(payload.get("jti"))

        stmt = select(Auth).where(Auth.user_id == self.user.id, Auth.jti_id == jti_id)
        result = await self.db_session.execute(stmt)
        auth_obj = result.scalar_one_or_none()

        assert auth_obj
        assert auth_obj.revoked == True

    @pytest.mark.asyncio
    async def test_signout_endpoint_failed_because_user_is_not_logged_in(self) -> None:
        """ Tests the failed case when the user is not logged in """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 401
            assert response.json()["detail"] == "Authorization failed: Authentication token could not be found."

    @pytest.mark.asyncio
    async def test_signout_endpoint_failed_because_db_error(self) -> None:
        """ Tests the failed case when a database error occurrs """
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.commit.side_effect = SQLAlchemyError("Broken database session")
        
        # Overwrite dependency
        api.dependency_overrides.clear()
        api.dependency_overrides[get_db] = lambda: broken_session

        with patch("routes.auth.signout.RefreshTokenVerifier.is_valid", new=AsyncMock(return_value=Auth)):
            async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
                response = await ac.post(self.path_url)
                assert response.status_code == 503
                assert response.json()["detail"] == "An unexpected error occurred: Please try again later."

    @pytest.mark.asyncio
    async def test_signout_endpoint_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        with patch("routes.auth.signout.RefreshTokenVerifier", side_effect=ValueError("Validation failed.")):
            async with AsyncClient(transport=self.transport, base_url=self.base_url, cookies=self.cookies) as ac:
                response = await ac.post(self.path_url)
                assert response.status_code == 400
                assert response.json()["detail"] == "An unexpected error occurred: Please try again later."