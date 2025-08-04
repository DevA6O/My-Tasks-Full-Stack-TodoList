from uuid import UUID
from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo
from security.jwt import decode_token, get_bearer_token
from database.connection import get_db
from routes.todo.t_utils import todo_exists, TodoExistCheckModel
from routes.todo.t_validation_model import TodoCreation as TodoCreationValidation

router = APIRouter()
logger = getLogger(__name__)

class TodoCreation:
    """ Class to create a new Todo """

    def __init__(self, db_session: AsyncSession, data: TodoCreationValidation, user_id: UUID) -> None:
        # Validate the class params
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session is not an AsyncSession")

        if not isinstance(user_id, UUID):
            raise ValueError("user_id is not a UUID")
        
        # Define the params for the class global
        self.db_session: AsyncSession = db_session
        self.data: TodoCreationValidation = data
        self.user_id: UUID = user_id

        self.title: str = self.data.title.strip()
        self.description: str = self.data.description.strip()
        

    async def _insert_new_todo(self) -> Todo | None:
        """ Helper-Method to save the todo in the user database.

        Returns:
        ---------
            - The created todo instance: Could be the instance of the Todo or None.
        """
        stmt = (
            insert(Todo)
            .values(user_id=self.user_id, title=self.title, description=self.description)
            .returning(Todo)
        )

        # Insert the data
        result_obj = await self.db_session.execute(stmt)
        todo_instance = result_obj.scalar_one_or_none()
        await self.db_session.commit()

        # Check whether the insert was successful
        if todo_instance:
            await self.db_session.refresh(todo_instance)
        
        return todo_instance

    async def create(self) -> Tuple[Todo | None, str]:
        """ Method to create the todo for the user
         
        Returns:
        ---------
            - The instance of the created todo or None
            - A string
        """
        try:
            # Check whether the todo (title) is already exist
            check_data = TodoExistCheckModel(user_id=self.user_id, title=self.title)

            if await todo_exists(data=check_data, db_session=self.db_session):
                return None, f"Todo ({self.title}) already exist."
            
            # Insert the todo if the todo is not exist
            todo = await self._insert_new_todo()

            if todo: # If the todo successfully got inserted
                return todo, f"Todo ({self.title}) successfully added."
            
        except IntegrityError as e: # Fallback if the insertion failed
            logger.exception(f"Insertion failed: {str(e)}", exc_info=True, extra={"user_id": self.user_id})
            return None, "Server error: Todo could not be created. Please try it later again."
        
        except SQLAlchemyError as e: # Fallback if the connection is closed or something else
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"user_id": self.user_id})
            return None, "Server error: An unexpected server error occurred. Please try it later again."

        return None, "Unknown error occurred: Todo could not be added."


@router.post("/api/todo/create")
async def create_todo_endpoint(
    data: TodoCreationValidation, token: str = Depends(get_bearer_token), 
    db_session: AsyncSession = Depends(get_db)
) -> None:
    """ Endpoint to create a new todo """
    # Define standard exception
    http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the user_id from token
        user_id: UUID = decode_token(token=token)

        # Create the todo
        todo_creation_service = TodoCreation(db_session=db_session, data=data, user_id=user_id)
        todo, message = await todo_creation_service.create()
        
        # Check whether the todo was created successfully.
        if todo is None:
            http_exception.detail = message
            raise http_exception
        
        # Return success response
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": message})
    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        http_exception.detail = str(e)
        raise http_exception