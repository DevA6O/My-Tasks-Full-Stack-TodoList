import pytest
import uuid
import pytest_asyncio
from unittest.mock import AsyncMock
from sqlalchemy import delete, insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
from routes.todo.t_home import TodoHome
from conftest import fake_username

@pytest_asyncio.fixture
async def fake_todo(fake_user: Tuple[User, AsyncSession]) -> Tuple[Todo, User, AsyncSession]:
    # Define the fake user and the fake db session
    user, db_session = fake_user

    stmt = (
        insert(Todo).values(
            title="Valid title",
            description="Valid description",
            user_id=user.id
        )
        .returning(Todo)
    )
    result = await db_session.execute(stmt)
    await db_session.commit()

    # Check whether the todo is successfully created or not
    todo_obj = result.scalar_one_or_none()

    if todo_obj is None:
        raise ValueError("Fake todo could not be created.")
    return (todo_obj, user, db_session)


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
    fake_todo: Tuple[Todo, User, AsyncSession]
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