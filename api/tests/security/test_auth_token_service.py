import uuid
import pytest
import pytest_asyncio
from fastapi import Request
from datetime import datetime, timezone
from unittest.mock import Mock
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from security.auth_token_service import StoreAuthToken, AuthTokenDetails

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
            expires_at=int(datetime.now(timezone.utc).timestamp())
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
            expires_at=int(datetime.now(timezone.utc).timestamp())
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
        import logging
        logging.info(params)
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