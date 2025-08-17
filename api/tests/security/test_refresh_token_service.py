import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, Mock, patch
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from typing import Tuple

from database.models import User, Auth
from security.refresh_token_service import (
    RefreshTokenService, is_refresh_token_valid,
    REFRESH_MAX_AGE
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