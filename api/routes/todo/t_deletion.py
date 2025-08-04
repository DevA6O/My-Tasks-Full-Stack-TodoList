import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from typing import Tuple

from routes.todo.t_validation_model import TodoDeletionModel
from routes.todo.t_utils import TodoExistCheckModel, todo_exists
from security.jwt import get_bearer_token, decode_token
from database.models import Todo
from database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_DELETION_ERROR_MSG: str = "Deletion failed: Todo could not be deleted for technical reasons. " \
"Please try again later."

class TodoDeletion:
    def __init__(self, data: TodoDeletionModel, db_session: AsyncSession, user_id: UUID) -> None:
        # Validate the class params
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
        
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be not None.")

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
        

@router.post("/api/todo/delete")
async def todo_deletion_endpoint(
    data: TodoDeletion, db_session: AsyncSession = Depends(get_db), 
    token: str = Depends(get_bearer_token)
) -> None:
    """ Endpoint to delete a todo """
    try:
        # Default http exception
        http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        # Fetches the user from the token
        user_id: UUID = decode_token(token=token)

        # Calls the delete method
        todo_deletion_service = TodoDeletion(data=data, db_session=db_session, user_id=user_id)
        success, msg = await todo_deletion_service.delete()

        # Checks whether the todo could not be deleted
        if not success:
            http_exception.detail = msg
            raise http_exception

        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": msg})
    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        http_exception.detail = DEFAULT_DELETION_ERROR_MSG
        raise http_exception