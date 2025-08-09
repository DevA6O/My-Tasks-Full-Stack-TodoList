import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple
from pydantic import BaseModel, ConfigDict

from database.models import User
from database.connection import get_db
from security.jwt import decode_token, get_bearer_token
from routes.todo.t_utils import validate_constructor

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_UNKNOWN_ERROR_MSG: str = "Unknown user: User could not be indentified."

class TodoHome():
    @validate_constructor
    def __init__(self, db_session: AsyncSession, user_id: UUID) -> None:
        self.user_id: UUID = user_id
        self.db_session: AsyncSession = db_session

    async def get_username_with_todos(self) -> Tuple[str | None, list, str | None]:
        """Fetches the username and todos for the user.

        Returns:
        --------
            Tuple[str, list, str]: A tuple containing:
                - The username as a string.
                - A list of todo items.
                - An error message if an error occurred, otherwise NoneType.
        """
        try:
            stmt: tuple = (
                select(User)
                .options(selectinload(User.todos))
                .where(User.id == self.user_id)
            )

            # Fetches the user object
            result = await self.db_session.execute(stmt)
            user_obj: User = result.scalar_one_or_none()

            # Checks whether the user could not be found
            if not user_obj:
                return None, [], DEFAULT_UNKNOWN_ERROR_MSG
            
            # Return the requested informations
            username: str = user_obj.name
            todos: list = user_obj.todos

            return username, todos, None
        except SQLAlchemyError as e: # Fallback, if an unexpected database error occurrs
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"user_id": self.user_id})
            return None, [], "Server error: Please try it later again."


class TodoSchema(BaseModel):
    """ Schema to return every todo correctly """
    id: UUID
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)

@router.post("/api/todo/get_all")
async def get_all_todos_endpoint(
    token: str = Depends(get_bearer_token), db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to get all todos """
    try:
        # Define standard http exception
        http_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=DEFAULT_UNKNOWN_ERROR_MSG
        )

        # Gets the user id from the token
        user_id: UUID = decode_token(token=token)

        # If the token has no user id
        if user_id is None:
            raise http_exception
        
        # Request to get the todos and the username
        todo_service = TodoHome(db_session=db_session, user_id=user_id)
        username, todos, error_msg = await todo_service.get_username_with_todos()

        # If an error is occurred
        if error_msg is not None:
            http_exception.detail = error_msg
            raise http_exception

        # Return response if no error is occurred
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={
                "username": username, 
                "todos": [todo.model_dump(mode="json") for todo in map(TodoSchema.model_validate, todos)]
            }
        )
    except ValueError as e: # Fallback
        logger.exception(str(e), exc_info=True)
        http_exception.detail = "An unexpected error occurred: Please try again later."
        raise http_exception