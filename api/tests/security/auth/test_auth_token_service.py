import uuid
import pytest
import pytest_asyncio
from fastapi import Request
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Auth
from security.auth.store_token_service import StoreAuthToken, AuthTokenDetails

class TestGetIpAddressMethod:
    """ Test class for different test scenarios for _get_ip_address method """

    @pytest.fixture(autouse=True)
    def setup(self, db_session: AsyncSession) -> None:
        """ Set up common test data """
        self.db_session = db_session
        self.data = AuthTokenDetails(
            user_id=uuid.uuid4(), 
            jti_id=uuid.uuid4(), 
            is_refresh_token=True, 
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )

    def test_get_ip_address_from_header_success(self) -> None:
        """ Test to get the ip address from header successful """
        mock_request = Mock()
        mock_request.__class__ = Request # <- to avoid validation errors
        mock_request.headers = {"x-forwarded-for": "123.000.123.000, 999.000.999.000"} # <- fake ips
        mock_request.client.host = "000.000.000.000" # function will should ignore this

        service = StoreAuthToken(request=mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        # The IP address is the first IP address, as we take the first 
        # IP address in the function.
        assert ip_address == "123.000.123.000" 

    def test_get_ip_address_from_client_host(self) -> None:
        """ Test to get the ip address from client host successful """
        mock_request = Mock()
        mock_request.__class__ = Request # <- to avoid validation errors
        mock_request.headers = {} # <- empty header
        mock_request.client.host = "999.999.999.999" # <- client ip address to fetch

        service = StoreAuthToken(request=mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        assert ip_address == "999.999.999.999"

    def test_get_ip_address_failed_because_no_ip_was_found(self) -> None:
        """ Test to get the ip address but no ip address could be found """
        mock_request = Mock()
        mock_request.__class__ = Request
        mock_request.headers = {}
        mock_request.client.host = None
        
        service = StoreAuthToken(request=mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        assert ip_address == ""


class TestExtractInformationsMethod:
    """ Test class for different test scenarios for _extract_informations method """

    @pytest.fixture(autouse=True)
    def setup(self, db_session: AsyncSession) -> None:
        """ Set up common test data """
        self.db_session = db_session
        self.data = AuthTokenDetails(
            user_id=uuid.uuid4(), 
            jti_id=uuid.uuid4(),
            is_refresh_token=True, 
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )

        self.user_agent_str: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/92.0.4515.131"
    
    def test_extract_informations_success(self) -> None:
        """ Tests the success case """
        mock_request = Mock()
        mock_request.__class__ = Request
        mock_request.headers = {"user-agent": self.user_agent_str}

        # Call the method to test
        ip_address = "123.123.123.123"
        service = StoreAuthToken(request=mock_request, data=self.data, db_session=self.db_session)
        stmt = service._extract_informations(ip_address=ip_address)

        # Compile the statement to check the values
        compiled = stmt.compile()
        params = compiled.params
        
        # Check the values
        assert params["ip_address"] == ip_address
        assert params["user_agent"].startswith("Mozilla")
        assert params["browser"] == "Chrome"
        assert params["device"] == "Other"
        assert params["os"] == "Windows"
        assert params["is_refresh_token"]
        
    def test_extract_informations_failed_because_no_user_agent(self) -> None:
        """ Tests the failed case when no user-agent is given """
        mock_request = Mock()
        mock_request.__class__ = Request
        mock_request.headers = {}

        # Call the method to test
        ip_address = "123.123.123.123"
        service = StoreAuthToken(request=mock_request, data=self.data, db_session=self.db_session)
        stmt = service._extract_informations(ip_address=ip_address)

        # Compile the statement to check the values
        compiled = stmt.compile()
        params = compiled.params

        # Check the values
        assert params["ip_address"] == "123.123.123.123"
        assert params["user_agent"] == ""
        assert params["device"] == "Other"
        assert params["browser"] == "Other"
        assert params["os"] == "Other"
        assert params["is_refresh_token"]


class TestStoreTokenMethod:
    """ Test class for different test scenarios for the store_token method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user
        self.data = AuthTokenDetails(
            user_id=self.user.id,
            jti_id=uuid.uuid4(),
            is_refresh_token=True,
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )
        self.user_agent_str = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) " \
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"

        # Define test values
        self.mock_request = Mock()
        self.mock_request.__class__ = Request
        self.mock_request.headers = {"user-agent": self.user_agent_str}
        self.mock_request.client.host = "123.456.789.000"

        self.service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)

    @pytest.mark.asyncio
    async def test_store_auth_success(self) -> None:
        """ Tests the success case """
        # Call the method
        result = await self.service.store_token()
        assert result

        # Check whether the insertion was actually successful
        stmt = select(Auth).where(
            Auth.user_id == self.user.id,
            Auth.jti_id == self.data.jti_id
        )
        db_result = await self.db_session.execute(stmt)
        auth_obj = db_result.scalar_one_or_none()
        
        assert auth_obj is not None
        assert auth_obj.device == "iPhone"
        assert auth_obj.browser == "Mobile Safari"
        assert auth_obj.os == "iOS"

    @pytest.mark.asyncio
    async def test_store_auth_failed_because_scalar_one_is_none(self) -> None:
        """ Tests the failed case when the insertion failed because 
        .scalar_one_or_none = None """
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(self.db_session, "execute", new=AsyncMock(return_value=mock_result)):
            result = await self.service.store_token()
            assert not result

    @pytest.mark.asyncio
    async def test_store_auth_failed_because_integrity_error(self) -> None:
        """ Tests the failed case when an IntegrityError error occurrs """
        # Store the token
        result = await self.service.store_token()
        assert result

        # Store the token again -> jti_id is already inserted -> IntegrityError occurrs
        new_result = await self.service.store_token()
        assert not new_result

    @pytest.mark.asyncio
    async def test_store_auth_failed_because_db_error_occurrs(self) -> None:
        """ Tests the failed case when the db session is broken """
        # Mock the db session
        broken_db_session = AsyncMock(wraps=self.db_session)
        broken_db_session.__class__ = AsyncSession
        broken_db_session.execute.side_effect = SQLAlchemyError("Broken database session")
        
        # Overwrite the current db session
        service = self.service
        service.db_session = broken_db_session
        
        # Start the test
        result = await self.service.store_token()
        assert not result