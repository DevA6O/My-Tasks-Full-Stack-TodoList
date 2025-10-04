import os
import uuid
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo, User
from database.connection import get_db
from security.auth.jwt import create_token, get_bearer_token
from routes.todo.t_completor import TodoCompletor, TodoCompletorModel
from main import api

load_dotenv()

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



class TestCompletorAPIEndpoint:
    """ Tests the creation api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
        """ Set up common test data """
        self.todo, self.user, self.db_session = fake_todo

        # Define default test values
        self.api_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/todo/complete"
        self.token: str = create_token(data={"sub": str(self.user.id)})

        # Set dependencies
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: self.token

        self.transport = ASGITransport(app=api)

    def teardown_method(self):
        api.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_completor_endpoint_success(self) -> None:
        """ Tests the success case when someone marked a todo as completed """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "todo_id": str(self.todo.id)
            }
            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_completor_endpoint_failed_because_validation_error(self) -> None:
        """ Tests the failed case when a ValidationError occurrs """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "todo_id": int(0)
            }

            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 422