import os
import uuid
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
from database.connection import get_db
from routes.todo.t_home import TodoHome
from security.jwt import get_bearer_token, create_token
from main import api

load_dotenv()


class TestGetUserWithTodosMethod:
    """ Test class for different test scenarios for the get_user_with_todos method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define service instance
        self.service = TodoHome(db_session=self.db_session, user_id=self.user.id)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("with_todos", [(True), (False)])
    async def test_get_user_with_todos_success(self, with_todos: bool) -> None:
        """ Tests the success case with todos and without todos """
        if not with_todos:
            # Deletes the todo for this test case
            from sqlalchemy import delete

            await self.db_session.execute((
                delete(Todo)
                .where(Todo.user_id == self.user.id, Todo.id == self.todo.id)
            ))

        # Start calling the method and checking the responses
        username, todos, error_msg = await self.service.get_username_with_todos()
        assert username == self.user.name
        assert error_msg is None

        if with_todos:
            assert todos[0].id == self.todo.id
        else:
            assert todos == []

    @pytest.mark.asyncio
    async def test_get_user_with_todos_failed_because_user_does_not_exist(self) -> None:
        """ Tests the failed case when a user does not exist """
        service = self.service
        service.user_id = uuid.uuid4() # <- Manipulates a fake user that does not exist

        username, todos, error_msg = await self.service.get_username_with_todos()
        assert username is None
        assert todos == []
        assert error_msg is not None

    @pytest.mark.asyncio
    async def test_get_user_with_todos_failed_because_db_error(self) -> None:
        """ Tests the failed case when a database error occurrs """
        broken_session = AsyncMock(wraps=self.db_session)
        broken_session.__class__ == AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Invalid db session")
        
        # Change the valid db_session to the invalid db_session
        self.service.db_session = broken_session

        # Start calling the method and checking the responses
        username, todos, error_msg = await self.service.get_username_with_todos()
        assert username is None
        assert todos == []
        assert error_msg is not None


class TestGetAllTodosAPIEndpoint:
    """ Test class for different scenarios for the api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Set up the test dependencies
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: create_token(data={"sub": str(self.user.id)})

        self.transport = ASGITransport(app=api)
        self.base_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/todo/get_all"

    def teardown_method(self) -> None:
        api.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_all_todos_endpoint_success(self) -> None:
        """ Tests the success case when no error occurrs """
        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json={})
            assert response.status_code == 200

        json_response = response.json()
        assert uuid.UUID(json_response["todos"][0]["id"]) == self.todo.id
    
    @pytest.mark.asyncio
    async def test_get_all_todos_endpoint_failed_because_invalid_token(self) -> None:
        """ Tests the failed case when a token has no sub """
        api.dependency_overrides[get_bearer_token] = lambda: create_token(data={"no_sub": str(self.user.id)})

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json={})
            assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_get_all_todos_endpoint_failed_because_validation_error(self) -> None:
        """ Tests the failed case when a validation error occurrs """
        api.dependency_overrides[get_db] = lambda: "Invalid db session"

        async with AsyncClient(transport=self.transport, base_url=self.base_url) as ac:
            response = await ac.post(self.path_url, json={})
            assert response.status_code == 400