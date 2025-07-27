import os
from dotenv import load_dotenv
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional
from httpx import AsyncClient, ASGITransport

from routes.auth.login import Login
from routes.auth.validation_models import LoginModel, RegisterModel
from database.models import User
from database.connection import get_db
from security.hashing import hash_pwd
from routes.auth.register import Register
from conftest import fake_email, fake_password, fake_hashed_password
from main import api

@pytest.mark.parametrize(
    "password_in_db, expected_value",
    [
        (fake_hashed_password, True), # Success
        (fake_hashed_password.encode("utf-8"), True), # Success with bytes
        ("not_a_hash", ValueError), # No bcrypt format
        (b"\x80\x81\x82", ValueError), # no decodeable bytes
        ("", ValueError), # empty string
        (12345, ValueError), # non-string input
    ]
)
def test_verify_password(password_in_db, expected_value) -> None:
    login_service = Login(
        db_session=None,
        data=LoginModel(email=fake_email, password=fake_password)
    )

    if isinstance(expected_value, bool):
        result = login_service.verify_password(password_in_db)
        assert result is expected_value
    else:
        with pytest.raises(expected_value):
            login_service.verify_password(password_in_db)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, is_registered, is_pwd_correct, expected_value",
    [
        (fake_email, fake_password, True, True, (User, "")),
        (fake_email, fake_password, True, False, (None, "")),
        (fake_email, fake_password, False, False, (None, ""))
    ]
)
async def test_authenticate(
    email: str, password: str, is_registered: bool, is_pwd_correct: bool,
    expected_value: Tuple[Optional[User], str], db_session: AsyncSession
) -> None:
    if is_registered:
        register_service = Register(
            db_session=db_session, 
            data=RegisterModel(username="FakeUsername", email=email, password=password)
        )
        result = await register_service.create_user()
        assert result is not None
    
    if not is_pwd_correct:
        password = "wrongPassword"

    login_service = Login(
        db_session=db_session,
        data=LoginModel(email=email, password=password)
    )
    user_obj, message = await login_service.authenticate()

    if isinstance(expected_value[0], type) and expected_value[0] is User:
        assert isinstance(user_obj, User)
    else:
        assert user_obj is expected_value[0]
    assert isinstance(message, str)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, expected_status_code",
    [
        (fake_email, fake_password, 200), # Successful login
        (fake_email, "wrongPassword", 400), # Incorrect password
        (str("notRegistered" + fake_email), fake_password, 400), # Not registered email
        (fake_email, "", 422), # Empty password
        (fake_email, "short", 422), # Invalid password (min-length = 8 = too short)
        (fake_email, str("tooLong." * 4) + ".", 422), # Invalid password (max-length = 32 = too long)
        ("", fake_password, 422), # Empty email
        ("notAnEmail", fake_password, 422), # Invalid email format
        (fake_email, "notAValidHashedPassword", 400), # Invalid hashed password format
    ]
)
async def test_login_endpoint(
    email: str, password: str, expected_status_code: int,
    fake_user: Tuple[User, AsyncSession]
) -> None:
    user, db_session = fake_user
    test_email = email if email == fake_email else email
    test_password = password if password == fake_password else password

    api.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=api)

    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
        payload: dict = {
            "email": test_email,
            "password": test_password
        }

        # Provoking error for invalid hashed password, if test password is not a valid hash
        if password == "notAValidHashedPassword":
            user.password = test_password
            await db_session.commit()

        response = await ac.post("/login", json=payload)
        assert response.status_code == expected_status_code