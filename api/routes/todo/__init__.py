from fastapi import APIRouter
from .t_home import router as HomeRouter
from .t_creation import router as TodoCreationRouter

TodoRouter = APIRouter()
TodoRouter.include_router(HomeRouter)
TodoRouter.include_router(TodoCreationRouter)