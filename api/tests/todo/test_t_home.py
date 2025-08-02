import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from routes.todo.t_home import TodoHome

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