import uuid
import pytest
import pytest_asyncio
from typing import Tuple
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from database.models import Todo, User
from routes.todo.t_editor import TodoEditor, TodoEditorModel


class TestTodoEditorUpdateMethod:
    """ Test class for different update scenarios """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data once for all test methods """
        self.todo, self.user, self.db_session = fake_todo

        # Create the services instance for the test
        self.data = TodoEditorModel(title="New title", description="New description", todo_id=self.todo.id)
        self.service = TodoEditor(data=self.data, db_session=self.db_session, user_id=self.user.id)

    @pytest.mark.asyncio
    async def test_update_successfully(self) -> None:
        """ Tests the success case """
        success, msg = await self.service.update()
        assert success
    
    @pytest.mark.asyncio
    async def test_update_failed_because_todo_does_not_exist(self) -> None:
        """ Tests the case if the update failed because the todo does not exist """
        # Manipulate the todo id with an invalid uuid
        self.service.data.todo_id = uuid.uuid4()

        success, msg = await self.service.update()
        assert not success
    
    @pytest.mark.asyncio
    async def test_update_failed_because_unknown_error(self) -> None:
        """ Tests the case if the update failed because of an unknown update error """
        # Manipulate the todo id with an invalid uuid
        self.service.data.todo_id = uuid.uuid4()

        with patch("routes.todo.t_editor.todo_exists", new=AsyncMock(return_value=True)):
            success, msg = await self.service.update()
            assert not success

    @pytest.mark.asyncio
    async def test_update_failed_because_db_error(self) -> None:
        """ Tests the case if the update failed because of a unexpected database error """
        # Manipulate the db session
        broken_session = AsyncMock(wraps=self.service.db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken db session")
        self.service.db_session = broken_session

        # Start the test with broken db session
        success, msg = await self.service.update()
        assert not success