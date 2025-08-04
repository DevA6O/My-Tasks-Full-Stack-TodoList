import logging
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, status

from routes.todo.t_utils import TodoExistCheckModel, todo_exists
from routes.todo.t_validation_model import TodoEditorModel
from database.connection import get_db
from database.models import Todo

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_UPDATE_FAILED_MSG: str = "Update failed: Todo could not be updated for technical reasons. " \
"Please try again later."

class TodoEditor:
    def __init__(self, data: TodoEditorModel, db_session: AsyncSession, user_id: UUID):
        # Validate class params
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
        
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        # Defines the class params globally
        self.db_session: AsyncSession = db_session
        self.user_id: UUID = user_id
        self.data: TodoEditorModel = data

    async def update(self):
        """ Method to update a todo for the user """
        try:
            # Checks whether the does not todo exists
            check_data = TodoExistCheckModel(user_id=self.user_id, todo_id=self.data.todo_id)

            if not await todo_exists(data=check_data, db_session=self.db_session):
                raise ValueError("Update failed: Todo could not be found.")
            
            # Update the todo
            stmt = (
                update(Todo)
                .where(Todo.user_id == self.user_id, Todo.id == self.data.todo_id)
                .values(title=self.data.title, description=self.data.description)
                .returning(Todo)
            )
            result = await self.db_session.execute(stmt)

            # Checks whether the update wasn't successfully
            updated_todo_obj = result.scalar_one_or_none()

            if not updated_todo_obj:
                logger.warning("Update failed: Unknown error occurred.", extra={
                    "user_id": self.user_id, "todo_id": self.data.todo_id
                })
                return False, DEFAULT_UPDATE_FAILED_MSG

            # If the update was successful
            await self.db_session.commit()
            return True, "Update successful: Todo successfully updated!"
        
        # Fallback if the database is broken or something else
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={
                "user_id": self.user_id, "todo_id": self.data.todo_id
            })
            return False, DEFAULT_UPDATE_FAILED_MSG