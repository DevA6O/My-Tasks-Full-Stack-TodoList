import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple, Optional

from routes.auth.login import Login
from routes.auth.validation_models import LoginModel, RegisterModel
from database.models import User
from security.hashing import hash_pwd
from routes.auth.register import Register

fake_email = "fake@email.com"
fake_password = "fakepassword"
correct_hash = hash_pwd(fake_password)

@pytest.mark.parametrize(
    "password_in_db, expected_value",
    [
        (correct_hash, True), # Success
        (correct_hash.encode("utf-8"), True), # Success with bytes
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