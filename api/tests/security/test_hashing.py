import pytest
from security.hashing import hash_pwd, is_hashed
from conftest import fake_password


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


# @pytest.mark.parametrize(
#     "password, expected_value",
#     [
#         ("FakePassword123", str),
#         (0, ValueError),
#     ]
# )
# def test_hash_pwd(password: str, expected_value: type) -> None:
#     if expected_value is ValueError:
#         with pytest.raises(ValueError):
#             hash_pwd(password)
#         return
    
#     hashed_password: str = hash_pwd(password)
#     assert isinstance(hashed_password, expected_value)


# # Hash test password for is_hashed test function
# test_hashed_pwd = hash_pwd("TestPassword123")

# @pytest.mark.parametrize(
#     "password, expected_value",
#     [
#         (test_hashed_pwd, True),
#         ("NotAHashedPassword", False)
#     ]
# )
# def test_is_hashed(password: str, expected_value: bool) -> None:
#     assert is_hashed(password) == expected_value