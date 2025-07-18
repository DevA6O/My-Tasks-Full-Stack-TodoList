import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from database import models # -> required to load every model
from database.connection import init_models
from exception_handler import validation_exception_handler
from routes.auth.register import router as RegisterRouter

logging.basicConfig(level=logging.INFO, format="[%(name)s | %(levelname)s] - %(asctime)s: %(message)s")

@asynccontextmanager
async def lifespan(api: FastAPI):
    # Load db models
    await init_models()
    yield

api = FastAPI(lifespan=lifespan)

# Add middleware
origins = [
    "http://localhost:5173"
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
api.include_router(RegisterRouter)