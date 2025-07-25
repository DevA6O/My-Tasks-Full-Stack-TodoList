import pytest
import pytest_asyncio
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession

from routes.auth.login import Login
from routes.auth.validation_models import LoginModel

fake_email = "fake@email.com"
fake_password = "fakepassword"
correct_hash = bcrypt.hashpw(fake_password.encode(), bcrypt.gensalt()).decode("utf-8")

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
def test_verify_password(password_in_db, expected_value):
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
async def test_authenticate(db_session: AsyncSession):
    pass