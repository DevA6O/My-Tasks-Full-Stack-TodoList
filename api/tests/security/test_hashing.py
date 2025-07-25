import pytest
from security.hashing import hash_pwd, is_hashed

@pytest.mark.parametrize(
    "password, expected_value",
    [
        ("FakePassword123", str),
        (0, ValueError),
    ]
)
def test_hash_pwd(password: str, expected_value: type):
    if expected_value is ValueError:
        with pytest.raises(ValueError):
            hash_pwd(password)
        return
    
    hashed_password = hash_pwd(password)
    assert isinstance(hashed_password, expected_value)


test_hashed_pwd = hash_pwd("TestPassword123")

@pytest.mark.parametrize(
    "password, expected_value",
    [
        (test_hashed_pwd, True),
        ("NotAHashedPassword", False)
    ]
)
def test_is_hashed(password: str, expected_value: bool):
    assert is_hashed(password) == expected_value