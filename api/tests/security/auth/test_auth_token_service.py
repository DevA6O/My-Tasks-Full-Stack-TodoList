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
from conftest import xForwarededFor, client_host, browser, os_family, device

class TestGetIpAddressMethod:
    """ Test class for different test scenarios for _get_ip_address method """

    @pytest.fixture(autouse=True)
    def setup(self, fake_request: Tuple[Request, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.mock_request, self.user, self.db_session = fake_request

        self.data = AuthTokenDetails(
            user_id=uuid.uuid4(), 
            jti_id=uuid.uuid4(), 
            is_refresh_token=True, 
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )


    def test_get_ip_address_from_header_success(self) -> None:
        """ Test to get the ip address from header successful """
        service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        # The IP address is the first IP address, as we take the first 
        # IP address in the function.
        assert ip_address == xForwarededFor.split(",")[0].strip()


    def test_get_ip_address_from_client_host(self) -> None:
        """ Test to get the ip address from client host successful """
        self.mock_request.headers = {}

        service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        assert ip_address == client_host


    def test_get_ip_address_failed_because_no_ip_was_found(self) -> None:
        """ Test to get the ip address but no ip address could be found """
        self.mock_request.headers = {}
        self.mock_request.client.host = None
        
        service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)
        ip_address = service._get_ip_address()

        assert ip_address == ""



class TestExtractInformationsMethod:
    """ Test class for different test scenarios for _extract_informations method """

    @pytest.fixture(autouse=True)
    def setup(self, fake_request: Tuple[Request, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.mock_request, self.user, self.db_session = fake_request
        self.ip_address = "999.888.777.666"

        self.data = AuthTokenDetails(
            user_id=uuid.uuid4(), 
            jti_id=uuid.uuid4(),
            is_refresh_token=True, 
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )


    def test_extract_informations_success(self) -> None:
        """ Tests the success case """
        service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)
        stmt = service._extract_informations(ip_address=self.ip_address)

        # Compile the statement to check the values
        compiled = stmt.compile()
        params = compiled.params
        
        # Check the values
        assert params["ip_address"] == self.ip_address
        assert params["user_agent"] == self.mock_request.headers["user-agent"]
        assert params["browser"] == browser
        assert params["device"] == device
        assert params["os"] == os_family
        assert params["is_refresh_token"]
        

    def test_extract_informations_failed_because_no_user_agent(self) -> None:
        """ Tests the failed case when no user-agent is given """
        self.mock_request.headers = {}

        # Call the method to test
        service = StoreAuthToken(request=self.mock_request, data=self.data, db_session=self.db_session)
        stmt = service._extract_informations(ip_address=self.ip_address)

        # Compile the statement to check the values
        compiled = stmt.compile()
        params = compiled.params

        # Check the values
        assert params["ip_address"] == self.ip_address
        assert params["user_agent"] == ""
        assert params["device"] == "Other"
        assert params["browser"] == "Other"
        assert params["os"] == "Other"
        assert params["is_refresh_token"]



class TestStoreTokenMethod:
    """ Test class for different test scenarios for the store_token method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_request: Tuple[Request, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.mock_request, self.user, self.db_session = fake_request
        self.data = AuthTokenDetails(
            user_id=self.user.id,
            jti_id=uuid.uuid4(),
            is_refresh_token=True,
            expires_at=int(datetime.now(timezone.utc).timestamp()) # <- only for the test
        )

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
        assert auth_obj.device == device
        assert auth_obj.browser == browser
        assert auth_obj.os == os_family

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