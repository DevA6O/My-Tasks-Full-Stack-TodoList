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
        """ Set up test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define default test values
        self.api_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/todo/update"
        self.token: str = create_token(data={"sub": str(self.user.id)})

        # Set dependencies
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: self.token

        self.transport = ASGITransport(app=api)

    def teardown_method(self):
        api.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_todo_update_endpoint_success(self) -> None:
        """ Tests the success case when someone updates a todo """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "title": "New title",
                "description": "New description",
                "todo_id": str(self.todo.id)
            }

            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 200

        # Checks whether the update was actually succcessful
        todo_obj = await check_update(user_id=self.user.id, todo_id=self.todo.id, db_session=self.db_session)
        assert todo_obj.title == payload["title"]
        assert todo_obj.description == payload["description"]

        
    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "title, description, valid_todo_id",
        [
            ("", "", True), # title too short
            ("X" * 141, "", True), # title too long
            ("Valid title", "X" * 321, True), # Description too long
            ("Valid title", "", False) # Invalid todo id
        ]
    )
    async def test_todo_update_endpoint_failed_because_validation_error(
        self, title: str, description: str, valid_todo_id: bool
    ) -> None:
        """ Tests the failed case if a validation error occurrs """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "title": title,
                "description": description,
                "todo_id": str(self.todo.id) if valid_todo_id else "Invalid todo id"
            }

            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 422