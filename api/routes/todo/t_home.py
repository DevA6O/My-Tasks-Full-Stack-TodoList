from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple
from pydantic import BaseModel, ConfigDict

from database.connection import get_db
from database.models import User
from security.jwt import decode_token, get_bearer_token

router = APIRouter()

class TodoHome():
    def __init__(self, db_session: AsyncSession, user_id: UUID) -> None:
        self.db_session: AsyncSession = db_session
        self.user_id: UUID = user_id

    async def get_user_with_todos(self) -> Tuple[str, list]:
        """ Returns the username and every todo the user have """
        stmt = (
            select(User)
            .options(selectinload(User.todos))
            .where(User.id == self.user_id)
        )
        result_obj = await self.db_session.execute(stmt)
        user: User = result_obj.scalar_one_or_none()

        if not user:
            return "Unknown User", []
        
        username: str = user.name
        todos: list = user.todos
        return username, todos


class TodoSchema(BaseModel):
    id: UUID
    title: str
    description: str

    model_config = ConfigDict(from_attributes=True)

@router.post("/api/todo/get_all")
async def get_all_todos(
    token: str = Depends(get_bearer_token), db_session: AsyncSession = Depends(get_db)
) -> None:
    """ Endpoint to get all todos """
    user_id: UUID = decode_token(token=token)

    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The user could not be identified.")
    
    todo_service = TodoHome(db_session=db_session, user_id=user_id)
    username, todos = await todo_service.get_user_with_todos()
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={
            "username": username, 
            "todos": [todo.model_dump(mode="json") for todo in map(TodoSchema.model_validate, todos)]
        }
    )