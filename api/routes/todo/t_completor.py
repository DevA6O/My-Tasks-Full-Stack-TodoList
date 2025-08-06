import logging
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from typing import Tuple

from database.models import Todo
from database.connection import get_db
from security.jwt import get_bearer_token, decode_token
from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from routes.todo.t_validation_model import TodoCompletorModel

logger = logging.getLogger(__name__)
router = APIRouter()

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
        

@router.post("/api/todo/complete")
async def completor_endpoint(
    data: TodoCompletorModel, token: str = Depends(get_bearer_token), 
    db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to mark a todo as completed """
    try:
        # Default http exception
        http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=DEFAULT_COMPLETION_ERROR_MSG)

        # Fetch user_id from token
        user_id: UUID = decode_token(token=token)

        # Start calling method
        service_completor = TodoCompletor(data=data, db_session=db_session, user_id=user_id)
        success, msg = await service_completor.mark_as_completed()

        # Check whether the todo could not be marked successfully
        if not success:
            http_exception.detail = msg
            raise http_exception
        
        raise JSONResponse(status_code=status.HTTP_200_OK, content={"message": msg})
    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        raise http_exception