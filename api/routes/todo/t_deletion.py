import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo
from database.connection import get_db
from security.jwt import get_bearer_token, decode_token
from routes.todo.t_validation_model import TodoDeletionModel, TodoExistCheckModel
from routes.todo.t_utils import (
    validate_constructor,
    run_todo_db_statement, RunTodoDbStatementContext,
    handle_todo_request, HandleTodoRequestModel
)

logger = logging.getLogger(__name__)
router = APIRouter()

DEFAULT_DELETION_ERROR_MSG: str = "Deletion failed: Todo could not be deleted for technical reasons. " \
"Please try again later."

class TodoDeletion:
    @validate_constructor
    def __init__(self, data: TodoDeletionModel, user_id: UUID, db_session: AsyncSession) -> None:
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
    """ Endpoint to delete a todo for an user """
    return await handle_todo_request(
        data_model=data, db_session=db_session,
        params=HandleTodoRequestModel(
            token=token, 
            service_class=TodoDeletion,
            service_method="delete",
            default_error_message=DEFAULT_DELETION_ERROR_MSG
        )
    )