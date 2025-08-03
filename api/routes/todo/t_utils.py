from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession

from routes.todo.t_validation_model import TodoExistCheckModel
from database.models import Todo

async def todo_exists(data: TodoExistCheckModel, db_session: AsyncSession) -> bool:
    """ Helper-Function to check whether the task already exists or not. 
    
    Returns:
    ---------
        - A boolean
    """
    if not isinstance(db_session, AsyncSession):
        raise ValueError("db_session must be an AsyncSession.")

    stmt = select(
        exists().where(Todo.user_id == data.user_id, Todo.title == data.title)
    )
    result = await db_session.execute(stmt)
    return result.scalar()