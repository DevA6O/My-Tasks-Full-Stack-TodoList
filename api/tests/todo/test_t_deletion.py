import os
import pytest
from dotenv import load_dotenv
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from httpx import AsyncClient, ASGITransport
from typing import Tuple

from routes.todo.t_deletion import TodoDeletion, TodoDeletionModel
from security.jwt import get_bearer_token, create_token
from database.connection import get_db
from database.models import User, Todo
from main import api

load_dotenv()

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_value, should_fail, raised_exception",
    [
        (True, False, False), # Success -> no problems
        (False, False, False), # Failed -> todo does not exists
        (False, True, False), # Failed -> deletion failed
        (False, False, True), # Failed -> A database error occurred
    ]
)
async def test_delete(
    expected_value: bool, should_fail: bool, raised_exception: bool,
    fake_todo: Tuple[Todo, User, AsyncSession]) -> None:
    # Defines the fake data
    todo, user, db_session = fake_todo

    # Calls the delete method
    data = TodoDeletionModel(todo_id=todo.id)
    todo_deletion_service = TodoDeletion(data=data, db_session=db_session, user_id=user.id)

    # Invalidate db session
    if raised_exception:
        broken_session = AsyncMock(wraps=db_session)
        broken_session.__class__ = AsyncSession
        broken_session.execute.side_effect = SQLAlchemyError("Broken DB Session")
        db_session = broken_session

    # Deletes the todo before the actually test started, if the current test want this
    if not expected_value:
        success, msg = await todo_deletion_service.delete()
        assert success

    # Checks whether the deletion should failed or not
    if should_fail:
        with patch("routes.todo.t_deletion.todo_exists", new=AsyncMock(return_value=True)):
            success, msg = await todo_deletion_service.delete()
    else:
        success, msg = await todo_deletion_service.delete()

    # Start checking the result
    assert success == expected_value
    assert isinstance(msg, str)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "should_fail, expected_status_code, raised_exception",
    [
        (False, 200, False), # Success -> deletion worked
        (True, 400, False), # Failed -> todo could not be found
        (True, 400, True) # Failed -> wrong type
    ]
)
async def test_todo_deletion_endpoint(
    should_fail: bool, expected_status_code: int, raised_exception: bool,
    fake_todo: Tuple[Todo, User, AsyncSession]
) -> None:
    # Defines the fake data
    todo, user, db_session = fake_todo

    # Create a user test token
    user_token = create_token(data={"sub": str(user.id)})

    # Overwrites dependencies
    if raised_exception:
        api.dependency_overrides[get_db] = lambda: AsyncSession
    else:
        api.dependency_overrides[get_db] = lambda: db_session
    
    api.dependency_overrides[get_bearer_token] = lambda: user_token

    # Start the request
    transport = ASGITransport(app=api)

    async with AsyncClient(transport=transport, base_url=os.getenv("VITE_API_URL")) as ac:
        payload: dict = {
            "todo_id": str(todo.id)
        }

        # Before starting the call, checking whether the request should failed
        if should_fail:
            data = TodoDeletionModel(todo_id=todo.id)
            todo_deletion_service = TodoDeletion(data=data, db_session=db_session, user_id=user.id)
            success, msg = await todo_deletion_service.delete()
            assert success

        # Starting final request and check the status_code
        response = await ac.post("/todo/delete", json=payload)
        assert response.status_code == expected_status_code