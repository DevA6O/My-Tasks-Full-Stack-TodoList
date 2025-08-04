import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import Tuple

from routes.todo.t_deletion import TodoDeletion, TodoDeletionModel
from database.models import User, Todo

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "expected_value, deletion_failed, raised_exception",
    [
        (True, False, False), # Success -> no problems
        (False, False, False), # Failed -> todo does not exists
        (False, True, False), # Failed -> deletion failed
        (False, False, True), # Failed -> A database error occurred
    ]
)
async def test_delete(
    expected_value: bool, deletion_failed: bool, raised_exception: bool,
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

    # Checks whether the deletion failed or not
    if deletion_failed:
        with patch("routes.todo.t_deletion.todo_exists", new=AsyncMock(return_value=True)):
            success, msg = await todo_deletion_service.delete()
    else:
        success, msg = await todo_deletion_service.delete()

    # Start checking the result
    assert success == expected_value
    assert isinstance(msg, str)