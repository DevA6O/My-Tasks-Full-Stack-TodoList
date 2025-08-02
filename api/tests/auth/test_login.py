import os
from dotenv import load_dotenv
import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional, Union
from httpx import AsyncClient, ASGITransport

from routes.auth.login import Login
from routes.auth.validation_models import LoginModel
from database.models import User
from database.connection import get_db
from conftest import fake_email, fake_password, fake_hashed_password
from main import api

load_dotenv()

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
def test_verify_password(
    db_session: AsyncSession, password_in_db: Union[str, bytes, int], 
    expected_value: Union[bool, Exception]
) -> None:
    # Defines the login service 
    login_service = Login(
        db_session=db_session,
        data=LoginModel(email=fake_email, password=fake_password)
    )

    # Starts the test
    if isinstance(expected_value, bool):
        result = login_service._verify_password(password_in_db)
        assert result is expected_value
    else:
        with pytest.raises(expected_value):
            login_service._verify_password(password_in_db)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, is_user_exist, expected_value",
    [
        (fake_email, fake_password, True, User), # Success
        (fake_email, fake_password, False, None), # User could not be found (is not registered)
    ]
)
async def test_get_user(
    email: str, password: str, is_user_exist: bool, expected_value: User | None,
    fake_user: Tuple[User, AsyncSession]
) -> None:
    # Defines the user and the db session
    user, db_session = fake_user

    # Removes the user if necessary
    if not is_user_exist:
        stmt = delete(User).where(User.id == user.id)
        await db_session.execute(stmt)

    # Defines the login service and start calling the method
    login_service = Login(
        db_session=db_session,
        data=LoginModel(email=email, password=password)
    )
    result = await login_service._get_user()

    # Start checking the result
    if expected_value is None:
        assert result is expected_value
    else:
        assert isinstance(result, expected_value)



@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, is_registered, is_pwd_correct, expected_value",
    [
        (fake_email, fake_password, True, True, (User, "")), # Success
        (fake_email, fake_password, True, False, (None, "")), # Incorrect password
        (fake_email, fake_password, False, False, (None, "")) # Not registered
    ]
)
async def test_authenticate(
    email: str, password: str, is_registered: bool, is_pwd_correct: bool,
    expected_value: Tuple[Optional[User], str], fake_user: Tuple[User, AsyncSession]
) -> None:
    # Defines the test values
    user, db_session = fake_user
    password: str = fake_password if is_pwd_correct else "WrongPassword"

    # Deletes the fake user if the test wants it 
    if not is_registered:
        stmt = delete(User).where(User.id == user.id)
        await db_session.execute(stmt)

    # Defines the login service and calls the authenticate methods
    login_service = Login(
        db_session=db_session,
        data=LoginModel(email=email, password=password)
    )
    user_obj, message = await login_service.authenticate()

    # Starts the test
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
    # Defines the test values   
    user, db_session = fake_user
    test_email = email if email == fake_email else email
    test_password = password if password == fake_password else password

    # Overrides the current dependencies
    api.dependency_overrides[get_db] = lambda: db_session
    transport = ASGITransport(app=api)

    # Starting the request
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

    # Clears the overrided dependencies
    api.dependency_overrides.clear()