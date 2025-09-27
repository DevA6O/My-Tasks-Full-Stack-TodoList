import os
import uuid
import pytest
import pytest_asyncio
from fastapi import Request
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport
from typing import Tuple

from security.auth.jwt import decode_token, create_token, get_bearer_token
from security.auth.refresh_token_service import RefreshTokenService
from database.models import User
from database.connection import get_db
from routes.settings.s_service import SettingsService
from main import api

# Fake mock request
mock_request = Mock()
mock_request.__class__ = Request # <- to avoid validation errors
mock_request.headers = {"x-forwarded-for": "123.000.123.000, 999.000.999.000"}
mock_request.client.host = "000.000.000.000"

class TestGetSessionsMethod:
    """ Test class for different test scenarios for _get_sessions method """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("current", [(True), (False)])
    async def test_get_sessions_success(self, current: bool, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Tests the success case """
        user, db_session = fake_user

        # Create a refresh token
        refresh_service = RefreshTokenService(request=mock_request, user_id=user.id, db_session=db_session)
        refresh_token: str = await refresh_service._create_and_store_refresh_token()

        # Start the test
        refresh_token_payload: dict = decode_token(token=refresh_token)
        session_id: str = str(refresh_token_payload.get("jti"))

        if not current:
            session_id: str = str(uuid.uuid4())

        payload: dict = {
            "sub": str(user.id),
            "session_id": session_id
        }

        service = SettingsService(payload=payload, db_session=db_session)
        sessions = await service._get_sessions()
        
        assert sessions != []
        assert sessions[0]["current"] if current else not sessions[0]["current"]

    
    @pytest.mark.asyncio
    async def test_get_sessions_failed_because_no_db_entry(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Tests the failed case when there is no entry in the database """
        user, db_session = fake_user

        payload: dict = {
            "sub": str(user.id),
            "session_id": str(uuid.uuid4())
        }

        service = SettingsService(payload=payload, db_session=db_session)
        sessions = await service._get_sessions()

        assert sessions == []


class TestGetUsernameAndEmailMethod:
    """ Test class for different test scenarios for _get_username_and_email method """

    @pytest.mark.asyncio
    async def test_get_username_and_email_success(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Tests the success case """
        user, db_session = fake_user

        payload: dict = {
            "sub": str(user.id),
            "session_id": str(uuid.uuid4()) 
        }

        service = SettingsService(payload=payload, db_session=db_session)
        username, email = await service._get_username_and_email()

        assert username is not None
        assert email is not None


    @pytest.mark.asyncio
    async def test_get_username_and_email_failed_because_no_db_entry(self, db_session: AsyncSession) -> None:
        """ Tests the failed case when there is no entry in the database """
        payload: dict = {
            "sub": str(uuid.uuid4()),
            "session_id": str(uuid.uuid4())
        }

        service = SettingsService(payload=payload, db_session=db_session)
        username, email = await service._get_username_and_email()
        
        assert username is None
        assert email is None



class TestGetMethod:
    """ Test class for different test scenarios for get method """

    @pytest.mark.asyncio
    async def test_get_success(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Tests the success case """
        user, db_session = fake_user

        # Create refresh token
        refresh_service = RefreshTokenService(request=mock_request, user_id=user.id, db_session=db_session)
        refresh_token: str = await refresh_service._create_and_store_refresh_token()

        # Start the test
        refresh_token_payload: dict = decode_token(token=refresh_token)
        payload: dict = {
            "sub": str(user.id),
            "session_id": str(refresh_token_payload.get("jti"))
        }

        service = SettingsService(payload=payload, db_session=db_session)
        returned_payload: dict = await service.get()

        assert returned_payload.get("username") == user.name
        assert returned_payload.get("email") == user.email
        assert returned_payload.get("sessions") != []


    @pytest.mark.asyncio
    async def test_get_failed_because_no_user_or_email(self, db_session: AsyncSession) -> None:
        """ Tests the error case when user or email is None """
        user_id: uuid.UUID = uuid.uuid4()

        payload: dict = {
            "sub": str(user_id),
            "session_id": str(uuid.uuid4())
        }

        service = SettingsService(payload=payload, db_session=db_session)
        
        with pytest.raises(ValueError) as exc_info:
            await service.get()

        assert str(exc_info.value) == "Authentication failed: User could not be identified."


    @pytest.mark.asyncio
    async def test_get_failed_because_db_error(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Tests the error case when a database error occurrs """
        user, db_session = fake_user

        payload: dict = {
            "sub": str(user.id),
            "session_id": str(uuid.uuid4())
        }

        # Mock db session
        broken_session = AsyncMock(wraps=db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken database session")

        # Start the test
        service = SettingsService(payload=payload, db_session=broken_session)
        returned_payload: dict = await service.get()
        
        assert returned_payload == {}



class TestSettingsServiceEndpoint:
    """ Test class for different test scenarios for settings_service_endpoint api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        api.dependency_overrides[get_db] = lambda: self.db_session

        self.transport = ASGITransport(app=api)
        self.base_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/settings/service"

        # Create refresh token
        refresh_service = RefreshTokenService(request=mock_request, user_id=self.user.id, db_session=self.db_session)
        refresh_token: str = await refresh_service._create_and_store_refresh_token()
        refresh_payload: dict = decode_token(token=refresh_token)
        self.session_id: str = str(refresh_payload.get("session_id"))

        token: str = create_token(data={"sub": str(self.user.id), "jti": str(uuid.uuid4()), "session_id": self.session_id})

        api.dependency_overrides[get_bearer_token] = lambda: token

    def teardown_method(self) -> None:
        api.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_settings_service_endpoint_success(self) -> None:
        """ Tests the success case """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 200
            assert response.json()["informations"]["username"] == self.user.name
            assert response.json()["informations"]["email"] == self.user.email
            assert response.json()["informations"]["sessions"] != []

    @pytest.mark.asyncio
    async def test_settings_service_endpoint_failed_because_no_data(self) -> None:
        """ Tests the failed case when no data could be retrieved """
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken database session")

        api.dependency_overrides[get_db] = lambda: broken_session

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 400
            assert response.json()["detail"] == "Loading failed: An unknown error has occurred. Please try again later."

    @pytest.mark.asyncio
    async def test_settings_service_endpoint_failed_because_type_error(self) -> None:
        """ Tests the failed case when a TypeError occurrs """
        with patch("routes.settings.s_service.decode_token", new=Mock(return_value=False)):
            async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
                response = await ac.post(self.path_url)
                assert response.status_code == 500
                assert response.json()["detail"] == "Server error: A server error has occurred. Please try again later."

    @pytest.mark.asyncio
    @pytest.mark.parametrize("reason", [("sub"), ("jti")])
    async def test_settings_service_endpoint_failed_because_value_error(self, reason: str) -> None:
        """ Tests the failed case when a ValueError occurrs """
        if reason == "sub":
            token: str = create_token(data={"session_id": self.session_id})
        elif reason == "jti":
            token: str = create_token(data={"sub": str(self.user.id)})

        api.dependency_overrides[get_bearer_token] = lambda: token

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url)
            assert response.status_code == 400

            if reason == "sub":
                assert response.json()["detail"] == "Authentication failed: User could not be identified."
            else:
                assert response.json()["detail"] == "Authentication failed: Server could not verify the user."