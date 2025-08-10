from uuid import UUID
from logging import getLogger
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo
from database.connection import get_db
from security.jwt import get_bearer_token
from shared.decorators import validate_constructor
from routes.todo.t_utils import (
    run_todo_db_statement, RunTodoDbStatementContext,
    handle_todo_request
)
from routes.todo.t_validation_models import (
    TodoCreationModel, TodoExistCheckModel,
    HandleTodoRequestModel
)

router = APIRouter()
logger = getLogger(__name__)

DEFAULT_UPDATE_FAILED_MSG: str = "Creation failed: Todo could not be created for technical reasons. " \
"Please try again later."

class TodoCreation:
    """ Class to create a new Todo """
    @validate_constructor
    def __init__(self, data: TodoCreationModel, user_id: UUID, db_session: AsyncSession) -> None:
        # Define the params for the class global
        self.db_session: AsyncSession = db_session
        self.data: TodoCreationModel = data
        self.user_id: UUID = user_id

        self.title: str = self.data.title.strip()
        self.description: str = self.data.description.strip()
        

    async def create(self) -> Tuple[bool, str]:
        """ Method to create the todo for the user
         
        Returns:
        ---------
            - A boolean: To check whether the deletion was successful or not
            - A string containing the deletion information
        """
        return await run_todo_db_statement(
            ctx=RunTodoDbStatementContext(
                data=TodoExistCheckModel(
                    user_id=self.user_id,
                    title=self.data.title,
                ),
                db_statement=(
                    insert(Todo)
                    .values(user_id=self.user_id, title=self.title, description=self.description)
                    .returning(Todo)
                ),
                db_session=self.db_session,
                should_todo_exist=False,
                success_msg="Creation successful: Todo successfully created.",
                default_error_msg=DEFAULT_UPDATE_FAILED_MSG,
                execution_type="Creation"
            )
        )


@router.post("/api/todo/create")
async def create_todo_endpoint(
    data: TodoCreationModel, token: str = Depends(get_bearer_token), 
    db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to create a new todo """
    return await handle_todo_request(
        data_model=data, db_session=db_session,
        params=HandleTodoRequestModel(
            token=token, service_class=TodoCreation, service_method="create",
            default_error_message=DEFAULT_UPDATE_FAILED_MSG
        )
    )