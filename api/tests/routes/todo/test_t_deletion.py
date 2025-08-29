import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport
from typing import Tuple

from routes.todo.t_deletion import TodoDeletion, TodoDeletionModel
from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from security.jwt import get_bearer_token, create_token
from database.connection import get_db
from database.models import User, Todo
from main import api

load_dotenv()


class TestDeleteMethod:
    """ Test class for the delete method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define service instance
        self.data = TodoDeletionModel(todo_id=self.todo.id)
        self.service = TodoDeletion(data=self.data, db_session=self.db_session, user_id=self.user.id)

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """ Tests the success case for deleting a todo """
        success, msg = await self.service.delete()
        assert success
        
        # Checks whether the todo does not exist anymore
        assert not await todo_exists(
            data=TodoExistCheckModel(
                user_id=self.user.id,
                todo_id=self.todo.id
            ),
            db_session=self.db_session
        )

class TestDeleteAPIEndpoint:
    """ Tests the deletion api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define default test values
        self.api_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/todo/delete"
        self.token: str = create_token(data={"sub": str(self.user.id)})

        # Set dependencies
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: self.token

        self.transport = ASGITransport(app=api)

    def teardown_method(self):
        api.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_todo_deletion_endpoint_success(self) -> None:
        """ Tests the success case when someone deletes a todo """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            response = await ac.post(url=self.path_url, json={"todo_id": str(self.todo.id)})
            assert response.status_code == 200

        # Checks whether the todo is actually deleted successfully
        assert not await todo_exists(
            data=TodoExistCheckModel(user_id=self.user.id, todo_id=self.todo.id), 
            db_session=self.db_session
        )
        
    @pytest.mark.asyncio
    async def test_todo_deletion_endpoint_failed_because_validation_error(self) -> None:
        """ Tests the failed case if a validation error occurrs """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            response = await ac.post(url=self.path_url, json={"todo_id": "No UUID"})
            assert response.status_code == 422