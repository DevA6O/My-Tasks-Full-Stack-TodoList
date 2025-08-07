import pytest
import uuid
import os
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
from database.connection import get_db
from routes.todo.t_creation import TodoCreation, TodoCreationModel
from security.jwt import create_token, get_bearer_token
from main import api

# Load env
load_dotenv()

# Define fake data
fake_title: str = "Valid title"
fake_description: str = "Valid description"
data = TodoCreationModel(title=fake_title, description=fake_description)











@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title, description, valid_token, can_created, expected_status_code",
    [
        (fake_title, fake_description, True, True, 200), # Success
        ("x", fake_description, True, False, 422), # Title is not valid (too short)
        (fake_title*50, fake_description, True, False, 422), # Title is not valid (too long)
        (fake_title, fake_description*50, True, False, 422), # Description is not valid (too long)
        (fake_title, fake_description, False, False, 400), # user token has no user 
        (fake_title, fake_description, True, False, 400), # todo cannot be created (todo already exist, for example)
    ]
)
async def test_create_todo_endpoint(
    title: str, description: str, valid_token: bool, expected_status_code: int,
    can_created: bool, fake_user: Tuple[User, AsyncSession]
) -> None:
    user, db_session = fake_user

    # Creates a user token
    if valid_token:
        user_token = create_token(data={"sub": str(user.id)})
    else:
        user_token = create_token(data={"no_sub": str(user.id)})
    
    # Mock the db_session and the user_token for the test
    api.dependency_overrides[get_db] = lambda: db_session
    api.dependency_overrides[get_bearer_token] = lambda: user_token
    transport = ASGITransport(app=api)

    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
        payload: dict = {
            "title": title,
            "description": description
        }

        # Create a fake todo
        if not can_created:
            todo_creation_service = TodoCreation(db_session=db_session, data=data, user_id=user.id)
            result = await todo_creation_service._insert_new_todo()
            assert result is not None

        # Start api request and test
        response = await ac.post("/todo/create", json=payload)
        assert response.status_code == expected_status_code

    # Clear the mocks
    api.dependency_overrides.clear()