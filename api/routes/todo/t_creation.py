from logging import getLogger
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Todo
from database.connection import get_db
from routes.todo.t_validation_model import TodoCreation as TodoCreationValidation

router = APIRouter()
logger = getLogger(__name__)

class TodoCreation:
    def __init__(self, db_session: AsyncSession, data: TodoCreationValidation) -> None:
        self.db_session: AsyncSession = db_session
        self.data: TodoCreationValidation = data

    async def insert_new_todo(self):
        """ Write the todo to the database """
        stmt = (
            insert(Todo)
            .values(title=self.data.title, description=self.data.description)
            .returning(Todo)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def is_todo_exist(self) -> bool:
        """ Check whether the task already exists or not. """
        stmt = select(Todo).where(Todo.user_id == self.data.user_id, Todo.title == self.data.title)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self):
        """ Creates a new todo """
        if await self.is_todo_exist():
            return None, f"Todo ({self.data.title}) already exist."

        try:
            todo = await self.insert_new_todo()

            if todo:
                return todo, f"Todo ({self.data.title}) successfully added."
        except IntegrityError as e:
            logger.exception(str(e), exc_info=True, extra={"user_id": self.data.user_id})
            return None, "Server error: Please try it later again."

        return None, "Unknown error occurred: Todo could not be added."


@router.post("/api/todo/create")
async def create_todo_endpoint(data: TodoCreationValidation, db_session: AsyncSession = Depends(get_db)):
    """ Endpoint to create a new todo """
    http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    creation_service = TodoCreation(db_session=db_session, data=data)
    todo, message = await creation_service.create()
    
    if todo is None:
        http_exception.detail = message
        raise http_exception
    
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"message": message}
    )