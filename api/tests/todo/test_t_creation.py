import os
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from database.connection import get_db
from security.jwt import create_token, get_bearer_token
from routes.todo.t_creation import TodoCreation, TodoCreationModel
from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from main import api

# Load env
load_dotenv()

class TestCreateMethod:
    """ Test class for the create method """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up test data """
        self.user, self.db_session = fake_user

        #  Define test values
        self.title: str = "Sport".strip()
        self.description: str = "More sports activity".strip()

        # Define service instance
        self.data = TodoCreationModel(title=self.title, description=self.description)
        self.service = TodoCreation(db_session=self.db_session, data=self.data, user_id=self.user.id)

    @pytest.mark.asyncio
    async def test_create_success(self):
        """ Tests that a todo is successfully created when it does not exist yet """
        success, msg = await self.service.create()
        assert success
        
        # Checks whether the todo is actually created successfully
        assert await todo_exists(
            data=TodoExistCheckModel(
                user_id=self.user.id, 
                title=self.title
            ), 
            db_session=self.db_session
        )



class TestCreateAPIEndpoint:
    """ Tests the creation api endpoint """

    @pytest_asyncio.fixture(autouse=True)
    async def setup(self, fake_user: Tuple[User, AsyncSession]) -> None:
        """ Set up test data """
        self.user, self.db_session = fake_user

        # Define default test values
        self.api_url: str = os.getenv("VITE_API_URL")
        self.path_url: str = "/todo/create"
        self.token: str = create_token(data={"sub": str(self.user.id)})

        # Set dependencies
        api.dependency_overrides[get_db] = lambda: self.db_session
        api.dependency_overrides[get_bearer_token] = lambda: self.token

        self.transport = ASGITransport(app=api)

    def teardown_method(self):
        api.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_todo_endpoint_success(self) -> None:
        """ Tests the success case when someone creates a todo """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "title": "Test title",
                "description": "Test description"
            }

            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "title, description",
        [
            ("", ""), # Title too short
            ("X" * 141, ""), # Title too long
            ("A valid title", "X" * 321), # Description too long
        ]
    )
    async def test_create_todo_endpoint_failed_because_validation_error(self, title: str, description: str) -> None:
        """ Tests the failed case when a ValidationError occurrs """
        async with AsyncClient(transport=self.transport, base_url=self.api_url) as ac:
            payload: dict = {
                "title": title,
                "description": description
            }

            response = await ac.post(url=self.path_url, json=payload)
            assert response.status_code == 422