import os
import uuid
import pytest
import pytest_asyncio
from pytest import LogCaptureFixture
from httpx import ASGITransport, AsyncClient
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Auth
from database.connection import get_db
from security.auth.jwt import get_bearer_token
from security.auth.jwt import create_token
from routes.settings.s_session_handler import SettingSessionsHandler
from main import api


class TestSettingSessionsHandlerClass:
    """ Test class to test the SettingSessionsHandler class """

    @pytest.fixture(autouse=True)
    def setup(
        self, fake_refresh_token_with_session_id: Tuple[str, str, Request, User, AsyncSession]
    ) -> None:
        """ Set up common test data """
        (
            self.refresh_token,
            self.session_id,
            self.mock_request,
            self.user,
            self.db_session
        ) = fake_refresh_token_with_session_id

        # Create fake token
        self.current_token: str = create_token(
            data={
                "sub": str(self.user.id),
                "session_id": str(self.session_id)
            }
        )

    def test_decode_was_successful(self) -> None:
        """ Tests the success case when the token could be decoded correctly 
        and the token has the required values """
        SettingSessionsHandler(
            jti_id=uuid.UUID(self.session_id),
            current_token=self.current_token,
            db_session=self.db_session
        )


    @pytest.mark.parametrize(
        "arg, log_msg",
        [
            ("db_session", "db_session must be an instance of AsyncSession."),
            ("jti_id", "jti_id must be an UUID."),
            ("current_token", "current_token must be a string.")
        ]
    )
    def test_trigger_type_error(self, arg: str, log_msg: str) -> None:
        """ Tests the failed case when a TypeError occurs """
        jti_id: uuid.UUID = uuid.UUID(self.session_id)
        current_token: str = self.current_token
        db_session: AsyncSession = self.db_session

        # Set the values
        if arg == "db_session":
            db_session = 0

        if arg == "jti_id":
            jti_id = 0

        if arg == "current_token":
            current_token = 0

        # Expect a TypeError
        with pytest.raises(TypeError) as exc_info:
            SettingSessionsHandler(
                jti_id=jti_id,
                current_token=current_token,
                db_session=db_session
            )

        assert str(exc_info.value) == log_msg


    def test_invalid_token(self) -> None:
        """ Tests the failed case when the token is invalid """
        with pytest.raises(ValueError) as exc_info:
            SettingSessionsHandler(
                jti_id=uuid.UUID(self.session_id),
                current_token="Invalid token", # <- to trigger the error
                db_session=self.db_session
            )
        
        assert str(exc_info.value) == "Invalid token: Token has no payload."


    def test_token_has_no_session_id(self) -> None:
        """ Tests the failed case when the token has no session id """
        current_token: str = create_token(
            data={
                "sub": str(self.user.id),
                # "session_id": str(self.session_id) <- to trigger the error
            }
        )

        with pytest.raises(ValueError) as exc_info:
            SettingSessionsHandler(
                jti_id=uuid.UUID(self.session_id),
                current_token=current_token,
                db_session=self.db_session
            )
        
        assert str(exc_info.value) == "session_id must be not None."


    def test_token_has_no_sub(self) -> None:
        """ Tests the failed case when the token has no sub """
        current_token: str = create_token(
            data={
                # "sub": str(self.user.id), <- to trigger the error
                "session_id": str(self.session_id)
            }
        )

        with pytest.raises(ValueError) as exc_info:
            SettingSessionsHandler(
                jti_id=uuid.UUID(self.session_id),
                current_token=current_token,
                db_session=self.db_session
            )
        
        assert str(exc_info.value) == "sub must be not None."


    def test_invalid_sub_type(self) -> None:
        """ Tests the failed case when sub (in the token) is not a UUID """
        current_token: str = create_token(
            data={
                "sub": str("Invalid type"), # <- to trigger the error
                "session_id": str(self.session_id)
            }
        )

        with pytest.raises(ValueError) as exc_info:
            SettingSessionsHandler(
                jti_id=uuid.UUID(self.session_id),
                current_token=current_token,
                db_session=self.db_session
            )
        
        assert str(exc_info.value) == "badly formed hexadecimal UUID string"



class TestRevokeMethod:
    """ Class for different test scenarios for the revoke method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, fake_refresh_token_with_session_id: Tuple[str, str, Request, User, AsyncSession]
    ) -> None:
        """ Set up common test data """
        (
            self.refresh_token,
            self.session_id,
            self.mock_request,
            self.user,
            self.db_session
        ) = fake_refresh_token_with_session_id

        # Create fake token
        self.current_token: str = create_token(
            data={
                "sub": str(self.user.id),
                "session_id": str(self.session_id)
            }
        )

    
    async def _get_revoke_entry(self, session_id: uuid.UUID) -> Auth:
        """ Fetch and return the revoke entry for the given session ID """
        from sqlalchemy import select

        statement = select(Auth).where(
            Auth.jti_id == uuid.UUID(session_id)
        )
        result_obj = await self.db_session.execute(statement=statement)
        return result_obj.scalar_one_or_none()

    
    @pytest.mark.asyncio
    async def test_revoke_success(self) -> None:
        """ Tests the success case where the session could be successfully revoked """
        current_token: str = create_token(
            data={
                "sub": str(self.user.id),
                "session_id": str(uuid.uuid4()) # <- to avoid triggering the session match
            }
        )

        self.handler = SettingSessionsHandler(
            jti_id=uuid.UUID(self.session_id),
            current_token=current_token,
            db_session=self.db_session
        )
        assert await self.handler.revoke()

        # Check whether the update was actually successful
        result: Auth = await self._get_revoke_entry(session_id=self.session_id)
        assert result.revoked


    @pytest.mark.asyncio
    async def test_revoke_failed_because_session_match(self) -> None:
        """ Tests the failed case when the current session should be revoked """
        self.handler = SettingSessionsHandler(
            jti_id=uuid.UUID(self.session_id),
            current_token=self.current_token,
            db_session=self.db_session
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await self.handler.revoke()

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "You cannot end the current session yourself. Please log out instead."

        # Check whether the update was actually unsuccessful
        result: Auth = await self._get_revoke_entry(session_id=self.session_id)
        assert not result.revoked


    @pytest.mark.asyncio
    async def test_revoke_failed_because_update_fails(self, caplog: LogCaptureFixture) -> None:
        """ Tests the failed case when the update fails """
        fake_jti_id: uuid.UUID = uuid.uuid4() # cause the update to fail

        self.handler = SettingSessionsHandler(
            jti_id=fake_jti_id,
            current_token=self.current_token,
            db_session=self.db_session
        )
        
        await self.handler.revoke()

        # Check the log message
        assert (
            "Update failed: The session could not be revoked successfully due to an unexpected update error."
        ) in caplog.text

        assert any(record.levelname == "WARNING" for record in caplog.records)

        # Check whether the update was actually unsuccessful
        result: Auth = await self._get_revoke_entry(session_id=self.session_id)
        assert not result.revoked



class TestRevokeEndpoint:
    """ Test class for different test scenarios for the revoke api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(
        self, fake_refresh_token_with_session_id: Tuple[str, str, Request, User, AsyncSession]
    ) -> None:
        """ Set up common test data """
        (
            self.refresh_token,
            self.session_id,
            self.mock_request,
            self.user,
            self.db_session
        ) = fake_refresh_token_with_session_id

        self.transport = ASGITransport(app=api)
        self.base_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/settings/session/revoke"

        # Create a fake token
        token = create_token(
            data={
                "sub": str(self.user.id),
                "jti": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4()) # to avoid trigger the session match exception
            }
        )

        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: token


    def teardown_method(self) -> None:
        api.dependency_overrides.clear()


    @pytest.mark.asyncio
    async def test_settings_revoke_session_endpoint_success(
        self, caplog: LogCaptureFixture
    ) -> None:
        """ Tests the success case where the session could be successfully revoked """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            payload: dict = {
                "jti_id": self.session_id
            }

            response = await ac.post(self.path_url, json=payload)
            assert response.status_code == 200

            # Check the log message and the extra parameter
            assert "Device successfully logged out." in caplog.text
            assert caplog.records[0].user_id
            assert caplog.records[0].jti_id
            assert caplog.records[0].token

    
    @pytest.mark.asyncio
    async def test_settings_revoke_session_endpoint_failed_because_session_match(
        self, caplog: LogCaptureFixture
    ) -> None:
        """ Tests the failed case where the session could not be successfully revoked
        because the current session could not be revoked """
        token = create_token(
            data={
                "sub": str(self.user.id),
                "jti": str(uuid.uuid4()),
                "session_id": str(self.session_id) # to trigger the session match
            }
        )
        api.dependency_overrides[get_bearer_token] = lambda: token

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            payload: dict = {
                "jti_id": self.session_id
            }

            response = await ac.post(self.path_url, json=payload)
            
            assert response.status_code == 403
            assert response.json()["detail"] == "You cannot end the current session yourself. Please log out instead." 

            # Check the log message and the extra parameter
            assert "User tried to revoke the current session" in caplog.text
            assert caplog.records[0].user_id
            assert caplog.records[0].jti_id
            assert caplog.records[0].token


    @pytest.mark.asyncio
    async def test_settings_revoke_session_endpoint_failed_because_update_fails(
        self, caplog: LogCaptureFixture
    ) -> None:
        """ Tests the failed case when the update, to revoke the session, fails """
        token = create_token(
            data={
                "sub": str(uuid.uuid4()), # <- to trigger a update error
                "jti": str(uuid.uuid4()),
                "session_id": str(uuid.uuid4())
            }
        )
        api.dependency_overrides[get_bearer_token] = lambda: token

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            payload: dict = {
                "jti_id": self.session_id
            }

            response = await ac.post(self.path_url, json=payload)
            
            assert response.status_code == 400
            assert response.json()["detail"] == "The device could not be logged out."

            # Check the log message and the extra parameter
            # assert "User tried to revoke the current session" in caplog.text
            assert caplog.records[0].user_id
            assert caplog.records[0].jti_id
            assert caplog.records[0].token


    @pytest.mark.asyncio
    async def test_settings_revoke_session_endpoint_failed_because_type_error(
        self, caplog: LogCaptureFixture
    ) -> None:
        """ Tests the failed case when the operation fails due to a TypeError """
        api.dependency_overrides[get_db] = lambda: "Invalid database session"

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            payload: dict = {
                "jti_id": self.session_id
            }

            response = await ac.post(self.path_url, json=payload)
            
            assert response.status_code == 400
            assert response.json()["detail"] == "The device could not be logged out."

            assert "db_session must be an instance of AsyncSession." in caplog.text