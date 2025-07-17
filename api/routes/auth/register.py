import bcrypt
import logging
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from .validation_models import RegisterModel

# Define global variables
router = APIRouter()
logger = logging.getLogger(__name__)


class Register:
    def __init__(self, db_session: AsyncSession, data: RegisterModel) -> None:
        self.db_session: AsyncSession = db_session
        self.data: RegisterModel = data

    def hash_pwd(self):
        """ Hashes the password """

    async def is_email_registered(self):
        """ Check if the email address is already registered or not """

    async def create_user(self):
        """ Create a new user """


@router.post("/api/register")
async def register(data: RegisterModel):
    """ Route to register a new user """
    return JSONResponse(
        status_code=status.HTTP_201_CREATED, content={
        "message": "Account successfully created."
    })