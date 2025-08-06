import logging
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from database.models import Todo
from t_validation_model import TodoCompletorModel

logger = logging.getLogger(__name__)

DEFAULT_COMPLETION_ERROR_MSG: str = "Completion failed: Todo could not be deleted for technical reasons. " \
"Please try again later."

class TodoCompletor:
    def __init__(self, data: TodoCompletorModel, db_session: AsyncSession, user_id: UUID) -> None:
        # Validate class params
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
        
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be an UUID.")

        self.data: TodoCompletorModel = data
        self.db_session: AsyncSession = db_session
        self.user_id: UUID = user_id

    async def mark_as_completed(self) -> Tuple[bool, str]:
        """ Method to mark a todo as completed 
        
        Returns:
        --------
            - A boolean: To check whether the completion was successful or not
            - A string containing the completion information
        """
        try:
            # Checks whether the todo does not exist
            check_data = TodoExistCheckModel(user_id=self.user_id, todo_id=self.data.todo_id)

            if not await todo_exists(data=check_data, db_session=self.db_session):
                return False, "Completion failed: Todo could not be found."

            # Mark as complete
            stmt = (
                update(Todo)
                .where(Todo.user_id == self.user_id, Todo.id == self.data.todo_id)
                .values(completed=True)
                .returning(Todo)
            )
            result = await self.db_session.execute(stmt)

            # Check whether the completion wasn't successfully
            todo_obj = result.scalar_one_or_none()

            if todo_obj is None:
                logger.warning("Completion failed: Unknown error occurred.", extra={
                    "user_id": self.user_id, "todo_id": self.data.todo_id
                })
                return False, DEFAULT_COMPLETION_ERROR_MSG
            
            # If the completion was successfully
            return True, "Completion successful: Todo marked as completed successfully."
        
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True)
            return False, DEFAULT_COMPLETION_ERROR_MSG