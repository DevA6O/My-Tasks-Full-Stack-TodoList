from fastapi import APIRouter
from routes.auth.login import router as LoginRouter
from routes.auth.register import router as RegisterRouter

AuthRouter = APIRouter()

AuthRouter.include_router(LoginRouter)
AuthRouter.include_router(RegisterRouter)