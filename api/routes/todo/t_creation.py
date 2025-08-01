from uuid import UUID
from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import Todo
from security.jwt import decode_token, get_bearer_token
from database.connection import get_db
from routes.todo.t_validation_model import TodoCreation as TodoCreationValidation

router = APIRouter()
logger = getLogger(__name__)

class TodoCreation:
    def __init__(self, db_session: AsyncSession, data: TodoCreationValidation, user_id: UUID) -> None:
        self.db_session: AsyncSession = db_session
        self.data: TodoCreationValidation = data
        self.title: str = self.data.title.strip()
        self.description: str = self.data.description.strip()
        self.user_id: UUID = user_id

    async def _insert_new_todo(self) -> Todo | None:
        """ Write the todo into the database. """
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

    async def _is_todo_exist(self) -> bool:
        """ Check whether the task already exists or not. """
        stmt = select(Todo).where(Todo.user_id == self.user_id, Todo.title == self.title)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self) -> Tuple[Tuple | None, str]:
        """ Creates a new todo. """
        # Check whether the todo (title) is already exist
        if await self._is_todo_exist():
            return None, f"Todo ({self.title}) already exist."

        try:
            # Insert the todo if the todo is not exist
            todo = await self._insert_new_todo()

            if todo: # If the todo successfully got inserted
                return todo, f"Todo ({self.title}) successfully added."
            
        # Fallback if insertion failed due to foreign keys or other reasons
        except IntegrityError as e:
            logger.exception(str(e), exc_info=True, extra={"user_id": self.user_id})
            return None, "Server error: Please try it later again."

        return None, "Unknown error occurred: Todo could not be added."


@router.post("/api/todo/create")
async def create_todo_endpoint(
    data: TodoCreationValidation, token: str = Depends(get_bearer_token), 
    db_session: AsyncSession = Depends(get_db)
) -> None:
    """ Endpoint to create a new todo """
    http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    try:
        user_id: UUID = decode_token(token=token)

        creation_service = TodoCreation(db_session=db_session, data=data, user_id=user_id)
        todo, message = await creation_service.create()
        
        if todo is None:
            http_exception.detail = message
            raise http_exception
        
        return JSONResponse(
            status_code=status.HTTP_200_OK, content={"message": message}
        )
    except ValueError as e:
        logger.exception(str(e), exc_info=True)
        http_exception.detail = str(e)
        raise http_exception