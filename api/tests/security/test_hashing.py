import pytest
from security.hashing import hash_pwd, is_hashed
from conftest import fake_password, fake_hashed_password


class TestHashPwd:
    """ Test class for different test scenarios for the hash_pwd function """

    def test_hash_pwd_success(self) -> None:
        """ Tests the success case """
        hashed_password: str = hash_pwd(password=fake_password)
        assert isinstance(hashed_password, str)

    def test_hash_pwd_failed_because_value_error(self) -> None:
        """ Tests the failed case when a ValueError occurrs """
        with pytest.raises(ValueError):
            hash_pwd(password=int(0))


class TestIsHashed:
    """ Test class for different test scenarios for the is_hashed function """

    def test_is_hashed_success(self) -> None:
        """ Tests the success case """
        assert is_hashed(fake_hashed_password)

    def test_is_hashed_failed_because_pwd_is_not_hashed(self) -> None:
        """ Tests the success case when a password is not hashed """
        assert not is_hashed(fake_password)