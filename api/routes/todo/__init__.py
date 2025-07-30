from fastapi import APIRouter
from .t_creation import router as TodoCreationRouter

TodoRouter = APIRouter()
TodoRouter.include_router(TodoCreationRouter)