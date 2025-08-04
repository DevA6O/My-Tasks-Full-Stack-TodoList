import pytest
import uuid
import os
from dotenv import load_dotenv
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy import delete, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
from database.connection import get_db
from routes.todo.t_home import TodoHome
from conftest import fake_username
from security.jwt import get_bearer_token, create_token
from main import api

load_dotenv()

@pytest.mark.parametrize(
    "valid_db_session, valid_user_id",
    [
        (True, True), # Success
        (False, True), # ValueError -> db_session is not an AsyncSession
        (True, False), # ValueError -> user_id is not a valid uuid
        (False, False), # ValueError -> user_id and db_session are invalid
    ]
)
def test_todo_home_class(
    valid_db_session: bool, valid_user_id: bool, fake_user: Tuple[User, AsyncSession]
) -> None:
    # Define the user and the db session
    user, db_session = fake_user
    user_id = user.id

    # Creates fake test data
    if not valid_db_session:
        db_session = False 

    if not valid_user_id:
        user_id = False

    # Test the failed case
    if not valid_db_session or not valid_user_id:
        with pytest.raises(ValueError):
            TodoHome(db_session=db_session, user_id=user_id)
        return
    
    # Test the success case
    TodoHome(db_session=db_session, user_id=user_id)



@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_user, valid_db_session, has_todos, expected_username, expected_todos, expected_error_msg",
    [
        (True, True, True, fake_username, True, None), # Success with todos
        (True, True, False, fake_username, False, None), # Success without todos
        (False, True, False, None, False, str), # Failed -> User does not exist
        (True, False, True, None, False, str), # Failed -> broken / invalid database session
    ]
)
async def test_get_user_with_todos(
    valid_user: bool, valid_db_session, has_todos: bool,
    expected_username: str, expected_todos: list[Todo | None], expected_error_msg: str,
    fake_todo: Tuple[Todo | None, User, AsyncSession]
) -> None:
    # Define the user and the db session
    todo, user, db_session = fake_todo
    user_id = user.id

    # Fake the current user_id
    if not valid_user:
        user_id = uuid.uuid4()

    # Fake the current db_session and make it "broken" / invalid
    if not valid_db_session:
        broken_session = AsyncMock(wraps=db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken db session")
        db_session = broken_session
    
    # Deletes the fake user's tasks if this is necessary for the test
    if not has_todos:
        stmt = delete(Todo).where(Todo.user_id == user_id, Todo.id == todo.id)
        await db_session.execute(statement=stmt)

    # Start the test
    todo_home_service = TodoHome(db_session=db_session, user_id=user_id)
    username, todos, error_msg = await todo_home_service.get_username_with_todos()

    # Start checking the response of the method
    assert username == expected_username
    assert bool(todos) == expected_todos

    if expected_error_msg is None:
        assert error_msg is expected_error_msg
    else:
        assert isinstance(error_msg, expected_error_msg)



@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_user_token, valid_user, valid_class_params, expected_status_code",
    [
        (True, True, True, 200), # Success
        (False, True, True, 400), # Invalid user token
        (True, False, True, 400), # Invalid user
        (True, True, False, 400), # Invalid class param(s)
    ]
)
async def test_get_all_todos_endpoint(
    valid_user_token: bool, valid_user: bool, valid_class_params: bool, 
    expected_status_code: int, fake_todo: Tuple[Todo, User, AsyncSession]
) -> None:
    # Define the fake todo, fake user and the fake db session
    todo, user, db_session = fake_todo
    user_id = user.id if valid_user else uuid.uuid4()

    # Define the usertoken
    if valid_user_token:
        user_token = create_token(data={"sub": str(user_id)}) # Valid
    else:
        user_token = create_token(data={"no_sub": str(user_id)}) # Invalid

    # Define the class parmas
    if valid_class_params:
        api.dependency_overrides[get_db] = lambda: db_session # Valid
    else:
        api.dependency_overrides[get_db] = lambda: AsyncSession # Invalid

    # Override the token with the created user token
    api.dependency_overrides[get_bearer_token] = lambda: user_token
    transport = ASGITransport(app=api)

    # Start the request
    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
        response = await ac.post("/todo/get_all", json={})
        status_code = response.status_code

        # Check the response
        assert status_code == expected_status_code

    api.dependency_overrides.clear()