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
from routes.todo.t_validation_model import TodoCompletorModel
from routes.todo.t_utils import (
    TodoExistCheckModel,
    run_todo_db_statement, RunTodoDbStatementContext,
    handle_todo_request, HandleTodoRequestModel
)

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
        return await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user_id,
                    todo_id=self.data.todo_id
                ),
                db_statement=(
                    update(Todo)
                    .where(Todo.user_id == self.user_id, Todo.id == self.data.todo_id)
                    .values(completed=True)
                    .returning(Todo)
                ),
                db_session=self.db_session,
                success_msg="Completion successful: Todo marked as completed successfully.",
                default_error_msg=DEFAULT_COMPLETION_ERROR_MSG,
                execution_type="Completion"
            )
        )
        

@router.post("/api/todo/complete")
async def completor_endpoint(
    data: TodoCompletorModel, token: str = Depends(get_bearer_token), 
    db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to mark a todo as completed """
    return await handle_todo_request(
        data_model=data, db_session=db_session,
        params=HandleTodoRequestModel(
            token=token,
            service_class=TodoCompletor,
            service_method="mark_as_completed",
            default_error_message=DEFAULT_COMPLETION_ERROR_MSG
        )
    )