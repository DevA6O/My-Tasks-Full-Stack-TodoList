import uuid
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from routes.todo.t_completor import TodoCompletor, TodoCompletorModel
from database.models import Todo, User

class TestTodoCompletorBaseMethod:
    """ Test class for different completion scenarios """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define service instance
        self.data = TodoCompletorModel(todo_id=self.todo.id)
        self.service = TodoCompletor(data=self.data, db_session=self.db_session, user_id=self.user.id)

    @pytest.mark.asyncio
    async def test_mark_as_completed_success(self) -> None:
        """ Tests the success case of the method """
        success, msg = await self.service.mark_as_completed()
        assert success

    @pytest.mark.asyncio
    async def test_mark_as_completed_failed_because_todo_does_not_exist(self) -> None:
        """ Tests the case if the todo does not exist """
        service = self.service
        service.data.todo_id = uuid.uuid4()
        
        success, msg = await service.mark_as_completed()
        assert not success

    @pytest.mark.asyncio
    async def test_mark_as_completed_failed_because_unknown_error(self) -> None:
        """ Tests the case if the method failed because of an unknown error """
        # Manipulate the todo id with an invalid uuid
        self.service.data.todo_id = uuid.uuid4()

        with patch("routes.todo.t_utils.todo_exists", new=AsyncMock(return_value=True)):
            success, msg = await self.service.mark_as_completed()
            assert not success

    @pytest.mark.asyncio
    async def test_mark_as_completed_failed_because_db_error(self) -> None:
        """ Tests the case if the method failed because of an unknown database error """
        # Manipulate the db session
        broken_session = AsyncMock(wraps=self.service.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken db session")
        self.service.db_session = broken_session

        # Start the test with broken db session
        success, msg = await self.service.mark_as_completed()
        assert not success