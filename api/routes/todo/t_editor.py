import logging
from uuid import UUID
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from typing import Tuple

from database.models import Todo
from database.connection import get_db
from security.jwt import get_bearer_token
from shared.decorators import validate_params
from routes.todo.t_validation_models import TodoEditorModel, TodoExistCheckModel
from routes.todo.t_utils import (
    run_todo_db_statement, RunTodoDbStatementContext,
    handle_todo_request, HandleTodoRequestModel
)

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_UPDATE_FAILED_MSG: str = "Update failed: Todo could not be updated for technical reasons. " \
"Please try again later."

class TodoEditor:
    @validate_params
    def __init__(self, data: TodoEditorModel, user_id: UUID, db_session: AsyncSession) -> None:
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
    """ Endpoint to update a todo for an user """
    return await handle_todo_request(
        data_model=data, db_session=db_session,
        params=HandleTodoRequestModel(
            token=token,
            service_class=TodoEditor,
            service_method="update",
            default_error_message=DEFAULT_UPDATE_FAILED_MSG
        )
    )