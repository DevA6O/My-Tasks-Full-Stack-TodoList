import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, Mock
from typing import Tuple

from database.models import User
from database.connection import get_db
from routes.auth.register import Register, RegisterModel, EmailAlreadyRegisteredException
from conftest import fake_username, fake_email, fake_password
from main import api

load_dotenv()


class TestIsEmailRegisteredMethod:
    """ Test class for different test scenarios for the _is_email_registered method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up test data """
        self.user, self.db_session = fake_user

        # Define service instance
        self.data = RegisterModel(
            username=fake_username,
            email=fake_email,
            password=fake_password
        )
        self.service = Register(db_session=self.db_session, data=self.data)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("is_registered", [(True), (False)])
    async def test_is_email_registered_success(self, is_registered: bool) -> None:
        """ Tests the success case when a email address is registered 
        and when a email address is not registered """
        service = self.service

        if not is_registered:
            service.data.email = "wrong@email.com"
        
        result = await service._is_email_registered()
        assert result == is_registered


class TestInsertUserIntoDbMethod:
    """ Test class for different test scenarios for the _insert_user_into_db method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, db_session: AsyncSession) -> None:
        """ Set up common test data """
        self.db_session = db_session

        # Define service instance
        self.data = RegisterModel(
            username=fake_username,
            email=fake_email,
            password=fake_password
        )
        self.service = Register(db_session=self.db_session, data=self.data)

    @pytest.mark.asyncio
    async def test_insert_user_into_db_success(self) -> None:
        """ Tests the success case """
        user_obj = await self.service._insert_user_into_db()
        assert isinstance(user_obj, User)

        assert user_obj.name == fake_username
        assert user_obj.email == fake_email

    @pytest.mark.asyncio
    async def test_insert_user_into_db_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs 
        because of the hashing process """
        with patch("routes.auth.register.hash_pwd", side_effect=ValueError("Password must be a string.")):
            user_obj = await self.service._insert_user_into_db()
            assert user_obj is None

    @pytest.mark.asyncio
    async def test_insert_user_into_db_failed_because_user_is_none(self) -> None:
        """ Tests the failed case when the user object is None """
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None

        with patch.object(self.db_session, "execute", new=AsyncMock(return_value=mock_result)):
            user_obj = await self.service._insert_user_into_db()
            assert user_obj is None
    

class TestCreateUserMethod:
    """ Test class for different test scenarios for the create_user method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define service instance
        self.data = RegisterModel(
            username=fake_username,
            email=fake_email,
            password=fake_password
        )
        self.service = Register(db_session=self.db_session, data=self.data)

    @pytest.mark.asyncio
    async def test_create_user_success(self) -> None:
        """ Tests the success case """
        service = self.service
        service.data.email = "not.registered@email.com"

        user_obj, message = await service.create_user()
        assert isinstance(user_obj, User)
        assert isinstance(message, str)

        assert user_obj.name == fake_username
        assert user_obj.email == service.data.email

    @pytest.mark.asyncio
    async def test_create_user_failed_because_email_is_registered(self) -> None:
        """ Tests the failed case when a email is already registered """
        with pytest.raises(EmailAlreadyRegisteredException) as exc_info:
            await self.service.create_user()
        
        assert exc_info.value is not None

    @pytest.mark.asyncio
    async def test_create_user_failed_because_integrity_error(self) -> None:
        """ Tests the failed case when a IntegrityError occurrs """
        with patch("routes.auth.register.Register._is_email_registered", new=AsyncMock(return_value=False)):
            user_obj, message = await self.service.create_user()
            assert user_obj is None
            assert isinstance(message, str)

    @pytest.mark.asyncio
    async def test_create_user_failed_because_database_error(self) -> None:
        """ Tests the failed case when a unknown database error occurrs """
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Invalid database session")

        service = self.service
        service.db_session = broken_session

        user_obj, message = await service.create_user()
        assert user_obj is None
        assert isinstance(message, str)


class TestRegisterAPIEndpoint:
    """ Test class for different test scenarios for the api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define test data
        self.data = RegisterModel(
            username=fake_username,
            email=fake_email,
            password=fake_password
        )

        # Set up the dependency
        api.dependency_overrides[get_db] = lambda: self.db_session

        self.transport = ASGITransport(app=api)
        self.base_url = os.getenv("VITE_API_URL")
        self.path_url = "/register"
        self.payload: dict = {
            "username": fake_username,
            "email": fake_email,
            "password": fake_password
        }

    def teardown_method(self) -> None:
        api.dependency_overrides.clear()
        
    @pytest.mark.asyncio
    async def test_register_endpoint_success(self) -> None:
        """ Tests the success case """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            payload = self.payload
            payload["email"] = "not.registered@email.com"

            response = await ac.post(self.path_url, json=payload)
            assert response.status_code == 201

            assert "set-cookie" in response.headers
            assert "refresh_token" in response.headers["set-cookie"]

    @pytest.mark.asyncio
    async def test_register_endpoint_failed_because_user_is_none(self) -> None:
        """ Tests the failed case when user object is None """
        with patch("routes.auth.register.Register.create_user", new_callable=AsyncMock) as mock_create_user:
            mock_create_user.return_value = (None, "Creation failed: ...")

            async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
                payload = self.payload
                payload["email"] = "not.registered@email.com"

                response = await ac.post(self.path_url, json=payload)
                assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_register_endpoint_failed_because_email_is_registered(self) -> None:
        """ Tests the failed case when the email is already registered """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json=self.payload)
            assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_register_endpoint_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        api.dependency_overrides[get_db] = lambda: "Invalid database session."

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json=self.payload)
            assert response.status_code == 400