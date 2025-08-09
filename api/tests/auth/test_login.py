import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional, Union
from httpx import AsyncClient, ASGITransport

from database.models import User
from database.connection import get_db
from conftest import fake_email, fake_password, fake_hashed_password
from routes.auth.login import Login
from routes.auth.validation_models import LoginModel
from main import api

load_dotenv()


class TestVerifyPasswordMethod:
    """ Test class for different scenarios for the _verify_password method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user
        
        # Define service instance
        self.data = LoginModel(email=fake_email, password=fake_password)
        self.service = Login(db_session=self.db_session, data=self.data)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("decoded", [(True), (False)])
    async def test_verify_password_success(self, decoded: bool) -> None:
        """ Tests the success case of the verify method 
        even though the 'password_in_db' is decoded or not """
        if decoded:
            success = self.service._verify_password(password_in_db=fake_hashed_password)
        else:
            success = self.service._verify_password(password_in_db=fake_hashed_password.encode("utf-8"))

        assert success

    @pytest.mark.asyncio
    async def test_verify_password_success_but_password_is_not_correct(self) -> None:
        """ Tests the success case of the verify method
        but the password which the user has entered is wrong """
        service = self.service
        service.data.password = "WrongPassword123"

        success = self.service._verify_password(password_in_db=fake_hashed_password)
        assert not success

    @pytest.mark.asyncio
    async def test_verify_password_failed_because_param_is_not_decodeable(self) -> None:
        """ Tests the failed case if the 'password_in_db' param 
        is not decodeable although it has the type 'bytes' """
        with pytest.raises(ValueError):
            self.service._verify_password(password_in_db=b"\x80\x81\x82") # b"\x80\x81\x82" is not decodeable with utf-8

    @pytest.mark.asyncio
    async def test_verify_password_failed_because_param_has_invalid_type(self) -> None:
        """ Tests the failed case if the param 'password_in_db' is not of the 
        type string or bytes """
        with pytest.raises(ValueError):
            self.service._verify_password(password_in_db=int(0))

    @pytest.mark.asyncio
    async def test_verify_password_failed_because_param_is_not_hashed(self) -> None:
        """ Tests the failed case if the param 'password_in_db' is not hashed """
        with pytest.raises(ValueError):
            self.service._verify_password(password_in_db="This password is not hashed.")


class TestGetUserMethod:
    """ Test class for different scenarios for the _get_user method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define service instance
        self.data = LoginModel(email=fake_email, password=fake_password)
        self.service = Login(db_session=self.db_session, data=self.data)

    @pytest.mark.asyncio
    async def test_get_user_success(self) -> None:
        """ Tests the success case when a user could found """
        user_obj = await self.service._get_user()
        assert isinstance(user_obj, User)

    @pytest.mark.asyncio
    async def test_get_user_success_but_user_could_not_found(self) -> None:
        """ Tests the success case when a user could not found """
        service = self.service
        service.data.email = "wrong@email.com"

        user_obj = await service._get_user()
        assert user_obj is None


class TestAuthenticateMethod:
    """ Test class for different test scenarios for the authenticate method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up common test data """
        self.user, self.db_session = fake_user

        # Define service instance
        self.data = LoginModel(email=fake_email, password=fake_password)
        self.service = Login(db_session=self.db_session, data=self.data)

    @pytest.mark.asyncio
    async def test_authenticate_success(self) -> None:
        """ Tests the success case """
        user_obj, message = await self.service.authenticate()
        assert isinstance(user_obj, User)
        assert isinstance(message, str)

    @pytest.mark.asyncio
    async def test_authenticate_failed_because_user_could_not_found(self) -> None:
        """ Tests the failed case when the user could not found """
        service = self.service
        service.data.email = "wrong@email.com"

        user_obj, message = await self.service.authenticate()
        assert user_obj is None
        assert isinstance(message, str)

    @pytest.mark.asyncio
    async def test_authenticate_failed_because_pwd_is_incorrect(self) -> None:
        """ Tests the failed case when the password is incorrect """
        service = self.service
        service.data.password = "WrongPassword123"

        user_obj, message = await self.service.authenticate()
        assert user_obj is None
        assert isinstance(message, str)

    @pytest.mark.asyncio
    async def test_authenticate_failed_because_invalid_db_session(self) -> None:
        """ Tests the failed case when a database session is invalid """
        from unittest.mock import AsyncMock
        from sqlalchemy.exc import SQLAlchemyError

        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Invalid database session")

        service = self.service
        service.db_session = broken_session

        user_obj, message = await self.service.authenticate()
        assert user_obj is None
        assert isinstance(message, str)


# @pytest.mark.asyncio
# @pytest.mark.parametrize(
#     "email, password, expected_status_code",
#     [
#         (fake_email, fake_password, 200), # Successful login
#         (fake_email, "wrongPassword", 400), # Incorrect password
#         (str("notRegistered" + fake_email), fake_password, 400), # Not registered email
#         (fake_email, "", 422), # Empty password
#         (fake_email, "short", 422), # Invalid password (min-length = 8 = too short)
#         (fake_email, str("tooLong." * 4) + ".", 422), # Invalid password (max-length = 32 = too long)
#         ("", fake_password, 422), # Empty email
#         ("notAnEmail", fake_password, 422), # Invalid email format
#         (fake_email, "notAValidHashedPassword", 400), # Invalid hashed password format
#     ]
# )
# async def test_login_endpoint(
#     email: str, password: str, expected_status_code: int,
#     fake_user: Tuple[User, AsyncSession]
# ) -> None:
#     # Defines the test values   
#     user, db_session = fake_user
#     test_email = email if email == fake_email else email
#     test_password = password if password == fake_password else password

#     # Overrides the current dependencies
#     api.dependency_overrides[get_db] = lambda: db_session
#     transport = ASGITransport(app=api)

#     # Starting the request
#     async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
#         payload: dict = {
#             "email": test_email,
#             "password": test_password
#         }

#         # Provoking error for invalid hashed password, if test password is not a valid hash
#         if password == "notAValidHashedPassword":
#             user.password = test_password
#             await db_session.commit()

#         response = await ac.post("/login", json=payload)
#         assert response.status_code == expected_status_code

#     # Clears the overrided dependencies
#     api.dependency_overrides.clear()