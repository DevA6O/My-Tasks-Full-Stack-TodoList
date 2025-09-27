from fastapi import APIRouter
from routes.auth.login import router as LoginRouter
from routes.auth.register import router as RegisterRouter
from routes.auth.signout import router as SignoutRouter

AuthRouter = APIRouter(prefix="/api")

AuthRouter.include_router(LoginRouter)
AuthRouter.include_router(RegisterRouter)
AuthRouter.include_router(SignoutRouter)