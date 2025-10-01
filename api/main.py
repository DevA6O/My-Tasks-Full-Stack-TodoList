import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from database.connection import init_models
from exception_handler import validation_exception_handler
from routes.auth import AuthRouter
from routes.todo import TodoRouter
from routes.settings import SettingsRouter
from security.auth.refresh_token_service import router as RefreshRouter

logging.basicConfig(level=logging.INFO, format="[%(name)s.py:%(lineno)d | %(levelname)s] - %(asctime)s: %(message)s")

@asynccontextmanager
async def lifespan(api: FastAPI):
    # Load db models
    await init_models()
    yield

api = FastAPI(lifespan=lifespan)

# Add middleware
origins = [
    "*" # CHANGE IT
]

api.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Add exception handler(s)
api.add_exception_handler(RequestValidationError, validation_exception_handler)

# Add routers 
api.include_router(AuthRouter)
api.include_router(TodoRouter)
api.include_router(RefreshRouter)
api.include_router(SettingsRouter)