import logging
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Tuple


from routes.todo.t_validation_model import TodoEditorModel, TodoExistCheckModel
from database.connection import get_db
from database.models import Todo
from security.jwt import get_bearer_token, decode_token
from routes.todo.t_utils import run_todo_db_statement, RunTodoDbStatementContext

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_UPDATE_FAILED_MSG: str = "Update failed: Todo could not be updated for technical reasons. " \
"Please try again later."

class TodoEditor:
    def __init__(self, data: TodoEditorModel, db_session: AsyncSession, user_id: UUID) -> None:
        # Validate class params
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
        
        if not isinstance(user_id, UUID):
            raise ValueError("user_id must be a UUID.")

        # Defines the class params globally
        self.db_session: AsyncSession = db_session
        self.user_id: UUID = user_id
        self.data: TodoEditorModel = data

    async def update(self) -> Tuple[bool, str]:
        """ Method to update a todo for the user 
        
        Returns:
        ---------
            - A boolean to check whether the update was successful or not
            - A detailed string
        """
        return await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user_id,
                    todo_id=self.data.todo_id
                ),
                db_statement=(
                    update(Todo)
                    .where(Todo.user_id == self.user_id, Todo.id == self.data.todo_id)
                    .values(title=self.data.title, description=self.data.description)
                    .returning(Todo)
                ),
                db_session=self.db_session,
                success_msg="Update successful: Todo successfully updated!",
                default_error_msg=DEFAULT_UPDATE_FAILED_MSG,
                execution_type="Update"
            )
        )


@router.post("/api/todo/update")
async def todo_update_endpoint(
    data: TodoEditorModel,
    db_session: AsyncSession = Depends(get_db), token: str = Depends(get_bearer_token),
) -> JSONResponse:
    """ Endpoint to update the todo for an user """
    try:
        # Default http exception
        http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        # Fetch the user from the token and define service instance
        user_id: UUID = decode_token(token=token)
        todo_editor_service = TodoEditor(data=data, db_session=db_session, user_id=user_id)

        # Start calling the update method and return response / expection
        success, msg = await todo_editor_service.update()

        if not success:
            http_exception.detail = str(msg)
            raise http_exception

        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": msg})
    except ValueError as e: # Fallback -> if decode_token failed or validation error in TodoEditor
        logger.exception(str(e), exc_info=True)
        http_exception.detail = DEFAULT_UPDATE_FAILED_MSG
        raise http_exception