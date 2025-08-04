from fastapi import APIRouter
from .t_home import router as HomeRouter
from .t_creation import router as TodoCreationRouter
from .t_deletion import router as TodoDeletionRouter

TodoRouter = APIRouter()
TodoRouter.include_router(HomeRouter)
TodoRouter.include_router(TodoCreationRouter)
TodoRouter.include_router(TodoDeletionRouter)