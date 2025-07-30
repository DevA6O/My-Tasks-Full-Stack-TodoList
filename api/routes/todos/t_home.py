from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db

fake_todos = [
    {"title": "Trash", "description": "Take out the trash", "id": 1},
    {"title": "Learning", "description": "Learn for the spanish test", "id": 2}
]

router = APIRouter()

class TodoHome():
    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session: AsyncSession = db_session

    async def _all_todos(self):
        """ Database query to get every todo from user """

    async def get_all(self):
        return fake_todos




@router.post("/api/todo/get_all")
async def get_all_todos(authorization: str = Header(None), db_session: AsyncSession = Depends(get_db)):
    """ Endpoint to get all todos """
    print(authorization[len("Bearer "):])
    return JSONResponse(
        status_code=status.HTTP_200_OK, content={"todos": fake_todos, "username": "DevA."}
    )