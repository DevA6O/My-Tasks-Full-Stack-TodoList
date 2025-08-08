import os
import uuid
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from typing import Tuple
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from httpx import ASGITransport, AsyncClient

from database.models import Todo, User
from database.connection import get_db
from routes.todo.t_editor import TodoEditor, TodoEditorModel
from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from security.jwt import create_token, get_bearer_token
from main import api

load_dotenv()

async def check_update(user_id: uuid.UUID, todo_id: uuid.UUID, db_session: AsyncSession) -> Todo:
    """ Global function which is returning the todo object 
    to check whether the update was successful or not """
    from sqlalchemy import select

    stmt = select(Todo).where(Todo.user_id == user_id, Todo.id == todo_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


class TestTodoEditorUpdateMethod:
    """ Test class for the update method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define test values
        self.title: str = "An updated title"
        self.description: str = "An updated description"

        # Define service instance
        self.data = TodoEditorModel(title=self.title, description=self.description, todo_id=self.todo.id)
        self.service = TodoEditor(data=self.data, db_session=self.db_session, user_id=self.user.id)

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """ Tests the success case for update method """
        success, msg = await self.service.update()
        assert success

        # Checks whether the update was successfully
        todo_obj = await check_update(user_id=self.user.id, todo_id=self.todo.id, db_session=self.db_session)
        assert todo_obj.title == self.title
        assert todo_obj.description == self.description


class TestTodoEditorUpdateEndpoint:
    """ Test class for different update scenarios with communicating via the api """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo
        self.token = create_token(data={"sub": str(self.user.id)})

        # Set default overrides
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: self.token

        self.transport = ASGITransport(app=api)
        self.base_url = os.getenv("VITE_API_URL")
        self.path_url = "/todo/update"

        # Define standard test payload
        self.payload: dict = {
            "title": "Valid Title",
            "description": "Valid Description",
            "todo_id": str(self.todo.id)
        }

    def teardown_method(self) -> None:
        """ Removes the overwritten dependencies before starting a new test case """
        api.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_update_successful(self) -> None:
        """ Tests the success update case """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json=self.payload)
            assert response.status_code == 200

            # Checks whether the update was actually successful
            todo_obj = await check_update(user_id=self.user.id, todo_id=self.todo.id, db_session=self.db_session)
            assert todo_obj.title == self.payload["title"]
            assert todo_obj.description == self.payload["description"]

    @pytest.mark.asyncio
    async def test_update_failed_because_todo_does_not_exist(self) -> None:
        """ Tests the failed case when the todo does not exist """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            # Overwrite the todo_id with an invalid id for the test
            payload: dict = self.payload.copy()
            payload["todo_id"] = str(uuid.uuid4())

            response = await ac.post(self.path_url, json=payload)
            assert response.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure_type", [("database"), ("token")])
    async def test_update_failed_because_value_error(self, failure_type: str) -> None:
        """ Tests the failed case if a ValueError occurred """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            # Overwrite the token or the db session with an invalid token or an invalid db session for the test
            if failure_type == "database":
                invalid_db_session: str = "INVALID_DB_SESSION"
                api.dependency_overrides[get_db] = lambda: invalid_db_session
            else:
                invalid_token: str = create_token(data={"no_sub": str(self.user.id)})
                api.dependency_overrides[get_bearer_token] = lambda: invalid_token

            response = await ac.post(self.path_url, json=self.payload)
            assert response.status_code == 400

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "failure_type, invalid_value", 
        [
            ("title", 0), # Invalid type
            ("title", ""), # too short
            ("title", "x" * 141), # too long
            ("description", 0), # Invalid type
            ("description", "x" * 321), # too long
            ("todo_id", 0) # Invalid type
        ]
    )
    async def test_update_failed_because_validation_error(self, failure_type: str, invalid_value: str | int) -> None:
        """ Tests the failed case if a ValidationError occurred """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            # Overwrite the payload with invalid types
            payload: dict = self.payload.copy()
            payload[failure_type] = invalid_value

            response = await ac.post(self.path_url, json=payload)
            assert response.status_code == 422