import pytest
import uuid
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
from routes.todo.t_creation import TodoCreation, TodoCreationValidation

# Define fake data
data = TodoCreationValidation(title="Valid title", description="Valid description")

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "valid_user, expected_exception",
    [
        (True, None), # Success
        (False, IntegrityError), # Failed -> user_id does not exist (forgein key error due to the db model connections)
    ]
)
async def test_insert_new_todo(
    valid_user: bool, expected_exception: Exception | None, fake_user: Tuple[User, AsyncSession]
) -> None:
    # Define the user and the db session
    user, db_session = fake_user
    user_id = user.id
    
    # Creates a fake user_id
    if not valid_user:
        user_id = uuid.uuid4()

    # Define the test data
    todo_creation_service = TodoCreation(db_session=db_session, data=data, user_id=user_id)

    # If we expect an error
    if expected_exception is not None:
        with pytest.raises(expected_exception):
            await todo_creation_service._insert_new_todo()
        return
    
    # Test the success case
    result = await todo_creation_service._insert_new_todo()
    assert result is not None
    assert result.user.id == user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "is_todo_exist, expected_value",
    [
        (False, None),
        (True, Todo),
    ]
)
async def test_is_todo_exist(
    is_todo_exist: bool, expected_value: type, fake_user: Tuple[User, Todo]
) -> None:
    # Define the user and the db session
    user, db_session = fake_user

    # Define the test data
    todo_creation_service = TodoCreation(db_session=db_session, data=data, user_id=user.id)

    # Create a test todo if the todo should be exist
    if is_todo_exist:
        result = await todo_creation_service._insert_new_todo()
        assert result is not None

    # Check if the todo exist or not
    result = await todo_creation_service._is_todo_exist()

    # Test the result
    if expected_value is None:
        assert result is expected_value
    else:
        assert isinstance(result, expected_value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "is_todo_exist, is_user_exist, expected_values",
    [
        (False, True, [Todo, str]), # Success
        (True, True, [None, str]), # Todo with the same title is not allowed 
        (False, False, [None, str]), # User does not exist
    ]
)
async def test_create(
    is_todo_exist: bool, is_user_exist: bool,
    expected_values: Tuple[Todo | None, str], fake_user: Tuple[User, AsyncSession]
) -> None:
    # Define the user and the db session
    user, db_session = fake_user
    user_id = user.id

    # Define the expected values
    expected_value_1 = expected_values[0]
    expected_value_2 = expected_values[1]

    # Create a fake invalid user
    if not is_user_exist:
        user_id = uuid.uuid4()

    # Define the fake data
    todo_creation_service = TodoCreation(db_session=db_session, data=data, user_id=user_id)

    # Create fake todo
    if is_todo_exist and is_user_exist:
        result = await todo_creation_service._insert_new_todo()
        assert result is not None
    
    # Start the test
    todo, message = await todo_creation_service.create()
    
    if expected_value_1 is None:
        assert todo is expected_value_1
    else:
        assert isinstance(todo, expected_value_1)

    assert isinstance(message, expected_value_2)