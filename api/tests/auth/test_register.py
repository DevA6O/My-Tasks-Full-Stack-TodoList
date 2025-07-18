import os
import pytest
from dotenv import load_dotenv
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import ValidationError
from sqlalchemy import select
from database.models import User
from routes.auth.register import Register
from routes.auth.validation_models import RegisterModel
from main import api

fake_username: str = "TestUser"
fake_email: str = "test@email.com"
fake_pwd: str = "secure_password123"

load_dotenv()

def test_hash_pwd(db_session: AsyncSession):
    data = RegisterModel(username=fake_username, email=fake_email, password=fake_pwd)
    register = Register(db_session=db_session, data=data)

    hashed = register.hash_pwd()
    assert hashed is not None
    assert isinstance(hashed, bytes)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, email, password, expected_value", 
    [
        (fake_username, fake_email, fake_pwd, True), # Success
        (fake_username, fake_email, fake_pwd, None), # No user
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
        assert is_registered
    else:
        is_registered = await register.is_email_registered()
        assert is_registered is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "username, email, password, expected_error",
    [
        (fake_username, fake_email, fake_pwd, None), # Success
        ("", fake_email, fake_pwd, ValidationError), # Min-Length Error for username
        (fake_username * 30, fake_email, fake_pwd, ValidationError), # Max-Length Error for username
        (fake_username, "test", fake_pwd, ValidationError), # No Email
        (fake_username, fake_email, "123456", ValidationError), # Min-Length Error for password
        (fake_username, fake_email, fake_pwd * 30, ValidationError), # Max-Length Error for password
        (fake_username, fake_email, fake_pwd, ValueError), # Duplicated account -> email address already registered
    ]
)
async def test_create_user(
    username: str, email: str, password: str, expected_error: Exception, db_session: AsyncSession
) -> None:
    # If the we expect a ValidationError
    if expected_error is ValidationError:
        with pytest.raises(expected_error):
            RegisterModel(username=username, email=email, password=password)
        return
    
    # Create a new user
    data = RegisterModel(username=username, email=email, password=password)
    register = Register(db_session=db_session, data=data)

    result = await register.create_user()
    assert result

    # Check whether the user exists in the database now
    stmt = select(User).where(User.email == email)
    result_obj = await db_session.execute(stmt)
    result = result_obj.scalar_one_or_none()
    assert result is not None

    # Check if the expected error is a ValueError
    if expected_error is ValueError:
        with pytest.raises(ValueError):
            await register.create_user()


@pytest.mark.asyncio
async def test_register_route(db_session: AsyncSession):
    async with AsyncClient(app=api, base_url=os.getenv("VITE_API_URL")) as ac:
        payload = {
            "username": fake_username,
            "email": fake_email,
            "password": fake_pwd
        }
        
        response = await ac.post("/register", json=payload)

        assert response.status_code == 201
        import logging
        logging.info(response)