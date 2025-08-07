import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo, User
from routes.todo.t_utils import TodoExistCheckModel, todo_exists


class TestTodoExists:
    """ Test class for different scenarios for the todo_exists function """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define differnt data models
        self.data_for_title = TodoExistCheckModel(user_id=self.user.id, title=self.todo.title)
        self.data_for_todoID = TodoExistCheckModel(user_id=self.user.id, todo_id=self.todo.id)
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("data_type", [("title"), ("todo_id")])
    async def test_todo_exists_success(self, data_type: str) -> None:
        """ Tests the search for the todo with the title or todo id """
        if data_type == "title":
            exists = await todo_exists(data=self.data_for_title, db_session=self.db_session)
        elif data_type == "todo_id":
            exists = await todo_exists(data=self.data_for_todoID, db_session=self.db_session)

        assert exists

    @pytest.mark.asyncio
    @pytest.mark.parametrize("data_type", [("title"), ("todo_id")])
    async def test_todo_exists_failed_because_todo_does_not_exist(self, data_type: str) -> None:
        """ Tests the failed case if the todo does not exist """
        import uuid

        if data_type == "title":
            self.data_for_title.todo_id = uuid.uuid4()
            exists = await todo_exists(data=self.data_for_title, db_session=self.db_session)
        elif data_type == "todo_id":
            self.data_for_todoID.todo_id = uuid.uuid4()
            exists = await todo_exists(data=self.data_for_todoID, db_session=self.db_session)

        assert not exists

    @pytest.mark.asyncio
    async def test_todo_exists_failed_because_db_session_is_invalid(self) -> None:
        """ Tests the failed case if the database session is invalid """
        with pytest.raises(ValueError):
            await todo_exists(data=self.data_for_title, db_session="Broken Database Session")