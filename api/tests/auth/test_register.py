import os
import pytest
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Tuple

from database.models import User
from database.connection import get_db
from routes.auth.register import Register, RegisterModel
from main import api

fake_username: str = "TestUser"
fake_email: str = "test@email.com"
fake_pwd: str = "secure_password123"

load_dotenv()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, email, password, expected_value", 
    [
        (fake_username, fake_email, fake_pwd, True), # Success
        (fake_username, fake_email, fake_pwd, False), # No user
    ]
)
async def test_is_email_registered(
    username: str, email: str, password: str, expected_value: str, db_session: AsyncSession
) -> None:
    data = RegisterModel(username=username, email=email, password=password)
    register = Register(db_session=db_session, data=data)

    if expected_value:
        await register.create_user()

    is_registered = await register.is_email_registered()
    assert is_registered == expected_value


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, email, password, expected_value, expected_exception",
    [
        (fake_username, fake_email, fake_pwd, [User, str], None), # Success
        (fake_username, fake_email, fake_pwd, [None, str], None), # Duplicated account -> email address already registered
        ("", fake_email, fake_pwd, None, ValidationError), # Min-Length Error for username
        (fake_username * 30, fake_email, fake_pwd, None, ValidationError), # Max-Length Error for username
        (fake_username, "test", fake_pwd, None, ValidationError), # No Email
        (fake_username, fake_email, "123456", None, ValidationError), # Min-Length Error for password
        (fake_username, fake_email, fake_pwd * 30, None, ValidationError), # Max-Length Error for password
    ]
)
async def test_create_user(
    username: str, email: str, password: str, expected_value: Tuple[User | None, str] | None, 
    expected_exception: Optional[Exception], db_session: AsyncSession
) -> None:
    # If the we expect a ValidationError
    if expected_exception is ValidationError:
        with pytest.raises(expected_exception):
            RegisterModel(username=username, email=email, password=password)
        return
    
    # Create a new user
    data = RegisterModel(username=username, email=email, password=password)
    register = Register(db_session=db_session, data=data)

    # Checks whether the creation has the expected value
    user_obj, msg = await register.create_user()
    assert isinstance(user_obj, User)
    assert isinstance(msg, str)

    # Checks whether the user now exists in the database
    stmt = select(User).where(User.email == email)
    result = await db_session.execute(stmt)
    result_obj = result.scalar_one_or_none()
    assert result_obj is not None

    # Test to create the same user if the test requires it
    if expected_value[0] is None:
        user_obj, msg = await register.create_user()
        assert user_obj is expected_value[0]
        assert isinstance(msg, expected_value[1])


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, email, password, expected_status_code, expected_exception",
    [
        (fake_username, fake_email, fake_pwd, 201, None), # Success
        (fake_username, fake_email, fake_pwd, 400, ValueError), # Email is already registered
    ]
)
async def test_register_endpoint(
    username: str, email: str, password: str, expected_status_code: int, 
    expected_exception: Optional[Exception], db_session: AsyncSession
) -> None:
    # Overwriting of the db_session
    api.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=api)

    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
        payload: dict = {
            "username": username,
            "email": email,
            "password": password
        }

        response = await ac.post("/register", json=payload)    

        if expected_exception:
            response = await ac.post("/register", json=payload)

        assert response.status_code == expected_status_code

    # Clears the overwriting
    api.dependency_overrides.clear()