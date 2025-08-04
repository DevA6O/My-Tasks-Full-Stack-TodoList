import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo, User
from routes.todo.t_utils import TodoExistCheckModel, todo_exists

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exists, title_or_id, expected_exception",
    [
        (True, "title", None), # Todo exists (checking with title)
        (True, "id", None), # Todo exists (checking with id)
        (False, "title", None), # Todo does not exists (checking with title)
        (False, "id", None), # Todo does not exists (checking with id)
        (False, "title", ValueError), # db_session is broken
    ]
)
async def test_todo_exists(
    exists: bool, title_or_id: str, expected_exception: Exception | None,
    fake_todo: Tuple[Todo, User, AsyncSession]
) -> None:
    # Defines the test values
    todo, user, db_session = fake_todo

    # Defines the data
    if title_or_id == "title":
        data = TodoExistCheckModel(user_id=user.id, title=todo.title)
    
    if title_or_id == "id":
        data = TodoExistCheckModel(user_id=user.id, todo_id=todo.id)

    # If we expect an error
    if expected_exception:
        with pytest.raises(expected_exception):
            await todo_exists(data=data, db_session="NO_VALID_DB_SESSION")
        return
    
    # If the todo should not exists -> delete it for the test
    if not exists:
        from sqlalchemy import delete

        stmt = delete(Todo).where(Todo.id == todo.id)
        await db_session.execute(stmt)
    
    # Start checking the result
    result = await todo_exists(data=data, db_session=db_session)
    assert result == exists