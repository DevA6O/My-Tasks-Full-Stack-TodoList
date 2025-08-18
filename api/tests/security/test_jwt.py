import jwt
import uuid
import time
import pytest
from datetime import datetime, timezone, timedelta

from security.jwt import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    get_bearer_token, decode_token, create_token
)


class TestGetBearerToken:
    """ Test class for different test scenarios for the get_bearer_token function """
    
    def test_get_bearer_token_success(self) -> None:
        """ Tests the success case """
        token: str = create_token(data={"sub": str(uuid.uuid4())})
        header: str = f"Bearer {token}"

        result = get_bearer_token(authorization=header)
        assert result == token
        
    def test_get_bearer_token_failed_because_no_token(self) -> None:
        """ Tests the error case when there is no token in the header """
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            get_bearer_token(authorization="")
        
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail


class TestDecodeToken:
    """ Test class for different test scenarios for the decode_token function """

    def test_decode_token_success(self) -> None:
        """ Tests the success case """
        user_id: uuid.UUID = uuid.uuid4()
        token: str = create_token(data={"sub": str(user_id)})
        
        payload: dict = decode_token(token=token)
        assert uuid.UUID(payload.get("sub")) == user_id

    def test_decode_token_failed_because_py_jwt_error(self) -> None:
        """ Tests the failed case when a PyJWTError occurrs """
        token: str = create_token(data={"sub": str(uuid.uuid4())}, expire_delta=timedelta(seconds=1))
        time.sleep(1.5) # Wait until the token is expired (invalid)

        result = decode_token(token=token)
        assert not result


class TestCreateToken:
    """ Test class for different test scenarios for the create_token function """

    @pytest.mark.parametrize("minutes", [(ACCESS_TOKEN_EXPIRE_MINUTES), (5)])
    def test_create_token_success(self, minutes: int) -> None:
        """ Tests the success case when an expiration date is set and when it is not """
        if minutes == ACCESS_TOKEN_EXPIRE_MINUTES:
            token: str = create_token(data={"sub": str(uuid.uuid4())})
        else:
            token: str = create_token(data={"sub": str(uuid.uuid4())}, expire_delta=timedelta(minutes=minutes))
        assert isinstance(token, str)

        # Tests the expiration
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)

        # Allows a deviation of 2 seconds
        assert abs((exp_datetime - expected_exp).total_seconds()) < 2

    @pytest.mark.parametrize("data", [(None, str("Not a dict"))])
    def test_create_token_failed_because_data_is_set_incorrect(self, data: str | None) -> None:
        """ Tests the failed case when the data is set incorrectly """
        with pytest.raises(ValueError):
            create_token(data=data)

    def test_create_token_failed_because_expire_delta_is_set_incorrect(self) -> None:
        """ Tests the failed case when expire_delta is set incorrectly """
        with pytest.raises(ValueError):
            create_token(data={"sub": str(uuid.uuid4())}, expire_delta=False)