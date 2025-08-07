import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from routes.todo.t_validation_model import TodoDeletionModel, TodoExistCheckModel
from routes.todo.t_utils import run_todo_db_statement, RunTodoDbStatementContext
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
        self.user_id: UUID = user_id
        self.db_session: AsyncSession = db_session

    async def delete(self) -> Tuple[bool, str]:
        """ Method to delete a todo for the user

        Returns:
        ---------
            - A boolean: To check whether the deletion was successful or not
            - A string containing the deletion information
        """
        return await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user_id,
                    todo_id=self.data.todo_id
                ),
                db_statement=(
                    delete(Todo)
                    .where(Todo.user_id == self.user_id, Todo.id == self.data.todo_id)
                    .returning(Todo)
                ),
                db_session=self.db_session,
                success_msg="Deletion successful: Todo successfully deleted!",
                default_error_msg=DEFAULT_DELETION_ERROR_MSG,
                execution_type="Deletion"
            )
        )



@router.post("/api/todo/delete")
async def todo_deletion_endpoint(
    data: TodoDeletionModel, db_session: AsyncSession = Depends(get_db), 
    token: str = Depends(get_bearer_token)
) -> JSONResponse:
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