import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from typing import Tuple

from routes.todo.t_validation_model import TodoDeletionModel
from routes.todo.t_utils import TodoExistCheckModel, todo_exists
from database.models import Todo

logger = logging.getLogger(__name__)

DEFAULT_DELETION_ERROR_MSG: str = "Deletion failed: Todo could not be deleted for technical reasons. " \
"Please try again later."

class TodoDeletion:
    def __init__(self, data: TodoDeletionModel, db_session: AsyncSession):
        # Validate the class param
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
        
        self.data: TodoDeletionModel = data
        self.db_session: AsyncSession = db_session

    async def delete(self) -> Tuple[bool, str]:
        """ Method to delete a todo for the user

        Returns:
        ---------
            - A boolean: To check whether the deletion was successful or not
            - A string containing the deletion information
        """

        try:
            # Checks whether the todo does not exists
            data = TodoExistCheckModel(user_id=self.data.user_id, todo_id=self.data.todo_id)

            if not todo_exists(data=data, db_session=self.db_session):
                return False, "Deletion failed: Todo could not be found."
            
            # Deletes the todo
            stmt = (
                delete(Todo).where(
                    Todo.user_id == self.data.user_id, Todo.id == self.data.todo_id
                ).returning(Todo)
            )
            result = await self.db_session.execute(stmt)

            # Checks whether the todo is successfully deleted
            deleted_todo_obj = result.scalar_one_or_none()

            if deleted_todo_obj is None:
                logger.warning("Deletion failed: Unknown error occurred.", extra={
                    "user_id": self.data.user_id, "todo_id": self.data.todo_id
                })
                return False, DEFAULT_DELETION_ERROR_MSG
            
            # If the deletion was successfully
            await self.db_session.commit()
            return True, "Deletion successful: Todo successfully deleted!"
        
        # Fallback solution (for the database)
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={
                "user_id": self.data.user_id, "todo_id": self.data.todo_id
            })
            return False, DEFAULT_DELETION_ERROR_MSG