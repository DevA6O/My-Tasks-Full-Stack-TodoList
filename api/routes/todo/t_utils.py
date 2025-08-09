import logging
from uuid import UUID
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dataclasses import dataclass
from fastapi import status, HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Tuple, TYPE_CHECKING
from sqlalchemy.sql import Executable

from routes.todo.t_validation_model import TodoExistCheckModel, HandleTodoRequestModel
from database.models import Todo
from security.jwt import decode_token

if TYPE_CHECKING:
    from routes.todo.t_validation_model import TodoExistCheckModel

logger = logging.getLogger(__name__)


def validate_constructor(method):
    """ Validator to validate the db_session and / or the user_id """
    from functools import wraps

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Fetches the db_session and user_id
        db_session = kwargs.get("db_session", None)
        user_id = kwargs.get("user_id", None)

        if db_session is not None and not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an instance of AsyncSession.")
        if user_id is not None and not isinstance(user_id, UUID):
            raise ValueError("user_id must be an instance of UUID.")
        
        return method(self, *args, **kwargs)
    
    return wrapper


async def todo_exists(data: TodoExistCheckModel, db_session: AsyncSession) -> bool:
    """ Helper-Function to check whether the task already exists or not. 
    
    Returns:
    ---------
        - A boolean
    """
    # Validate the db session
    if not isinstance(db_session, AsyncSession):
        raise ValueError("db_session must be an AsyncSession.")
    
    # Check what information is provided
    if data.todo_id:
        stmt = select(exists().where(Todo.user_id == data.user_id, Todo.id == data.todo_id))
    
    elif data.title:
        stmt = select(exists().where(Todo.user_id == data.user_id, Todo.title == data.title))
        
    # Start db request
    result = await db_session.execute(stmt)
    return result.scalar()



@dataclass
class RunTodoDbStatementContext:
    """ 
        Context container for executing the todo database statement

        Args:
            data (TodoExistCheckModel): Validated data input containing the
                user_id, title and the todo_id

            db_statement (Executable): An executable database statement 
                (Update, Delete or Insert)

            db_session (AsyncSession): An open and valid database session

            success_msg (str): The success message which should be returned
                if the execution was successful
            
            default_error_msg (str): A default error message which should be returned
                if the execution failed
            
            execution_type (str): Describes the tyoe of execution (e.g. Creation, Update, Deletion, ...)

            should_todo_exist (bool): If it is set to True, a todo with the title or id must exist. 
                Default is False.
    """

    data: "TodoExistCheckModel"
    db_statement: Executable
    db_session: AsyncSession
    success_msg: str
    default_error_msg: str
    execution_type: str
    should_todo_exist: bool = True

async def run_todo_db_statement(ctx: RunTodoDbStatementContext) -> Tuple[bool, str]:
    """
    Helper-Function to run a database statement for the todo

    Args:
        ctx (UpdateTodoContext): Context data for database operation

    Returns:
        tuple:
            - bool: Whether the operation was successful
            - str: A message describing the outcome
    """

    try:
        # Checks whether the todo does not exist but only if it is required
        if ctx.should_todo_exist:
            if not await todo_exists(data=ctx.data, db_session=ctx.db_session):
                return (False, f"{ctx.execution_type} failed: Todo could not be found.")

        # Execute the statement
        result = await ctx.db_session.execute(ctx.db_statement)
        todo_obj = result.scalar_one_or_none()

        # Check whether the execution was successfully
        if todo_obj is not None:
            await ctx.db_session.commit()

            logger.info(ctx.success_msg, extra={"user_id": ctx.data.user_id, "todo_id": todo_obj.id})
            return (True, ctx.success_msg)
        
        # If the execution wasn't successfully
        logger.warning(f"{ctx.execution_type} failed: Unknown error occurred.", extra={
            "user_id": ctx.data.user_id, "todo_id": ctx.data.todo_id
        })
    # Fallback exception handler if the database has problems
    except IntegrityError as e:
        logger.exception(f"Insertion failed: {str(e)}", exc_info=True)
    except SQLAlchemyError as e:
        logger.exception(f"Database error: {str(e)}", exc_info=True)
    
    return (False, ctx.default_error_msg)


async def handle_todo_request(
    data_model: Any, db_session: AsyncSession, params: HandleTodoRequestModel
) -> JSONResponse:
    """
        Helper-Function for todo api endpoints

        Args:
            data_model (Any): The Pydantic model passed to the endpoint
            db_session (AsyncSession): A open and valid database session
            params (HandleTodoRequestModel): A Pydantic model for the todo request 
                (see more information on the docs of this Pydantic model) 

        Returns:
            JSONResponse: A FastAPI response
    """
    # Default http exception
    http_exception = HTTPException(
        status_code=params.http_status_exception, 
        detail=params.default_error_message
    )

    try:
        # Validates the database session
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an instance of AsyncSession.")

        # Extract the user id from token
        user_id: UUID = decode_token(token=params.token)

        # Define service instance and method
        service = params.service_class(data=data_model, db_session=db_session, user_id=user_id)
        method = getattr(service, params.service_method)

        # Calls the method
        success, msg = await method()

        # Checks whether the call was successful
        if success:
            return JSONResponse(status_code=params.http_status_success, content={"message": msg})

        # If it wasn't successfully
        http_exception.detail = msg
    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        http_exception.detail = params.default_error_message

    raise http_exception