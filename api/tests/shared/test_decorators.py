import uuid
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from shared.decorators import validate_constructor

class TestValidateConstructor:
    """ Test class for different scenarios for the decorator """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up test data """
        self.user, self.db_session = fake_user

        class DummyService:
            @validate_constructor
            def __init__(self, db_session: AsyncSession = None, user_id: uuid.UUID = None) -> None:
                self.db_session: AsyncSession = db_session
                self.user_id: uuid.UUID = user_id

        self.dummy_service = DummyService

    @pytest.mark.asyncio
    async def test_validate_constructor_with_valid_params(self) -> None:
        """ Tests the success case with valid params """
        instance = self.dummy_service(db_session=self.db_session, user_id=self.user.id)
        assert instance.db_session == self.db_session
        assert instance.user_id == self.user.id

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_db_session, invalid_user_id", [(True, False), (False, True)])
    async def test_validate_constructor_with_invalid_params(
        self, invalid_db_session: bool, invalid_user_id: bool
    ) -> None:
        """ Tests the failed case when a parameter is set incorrectly """
        with pytest.raises(ValueError):
            if invalid_db_session:
                self.dummy_service(db_session="Invalid db session", user_id=self.user.id)
            elif invalid_user_id:
                self.dummy_service(db_session=self.db_session, user_id="not an UUID.")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure_arg", [("db_session"), ("user_id")])
    async def test_validate_constructor_with_only_one_invalid_param(
        self, failure_arg: str
    ) -> None:
        """ Tests the failed case when only one parameter is set incorrectly """
        with pytest.raises(ValueError):
            if failure_arg == "db_session":
                self.dummy_service(db_session="Invalid db session")
            elif failure_arg == "user_id":
                self.dummy_service(user_id="not an UUID.")

