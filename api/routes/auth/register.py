import bcrypt
import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database.models import User
from database.connection import get_db
from .validation_models import RegisterModel

router = APIRouter()
logger = logging.getLogger(__name__)


class Register:
    def __init__(self, db_session: AsyncSession, data: RegisterModel) -> None:
        self.db_session: AsyncSession = db_session
        self.data: RegisterModel = data

    def hash_pwd(self):
        """ Hashes the password """
        return bcrypt.hashpw(self.data.password.encode(), bcrypt.gensalt())

    async def is_email_registered(self) -> Optional[User]:
        """ Check if the email address is already registered or not """
        stmt = select(User).where(User.email == self.data.email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self):
        """ Create a new user """
        email_check = await self.is_email_registered()

        if email_check is not None:
            raise ValueError("E-mail address is already registered.")

        hashed_pwd: bytes = self.hash_pwd()
        stmt = insert(User).values(name=self.data.username, email=self.data.email, password=hashed_pwd)
        
        try:
            await self.db_session.execute(stmt)
            await self.db_session.commit()
        except IntegrityError: # Fallback -> for example the created id / email is the same
            logger.exception("Failed to create a new user", exc_info=True, extra={"email": self.data.email})
            await self.db_session.rollback()
            raise

        return True



@router.post("/api/register")
async def register(data: RegisterModel, db_session: AsyncSession = Depends(get_db)):
    """ Route to register a new user """
    http_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        register = Register(db_session=db_session, data=data)    
        is_created = await register.create_user()

        if is_created:
            msg: str = "Account successfully created"
            logger.info(msg, extra={"email": data.email})
            return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": msg})

        msg: str = "An unknown error occurred: Account cannot be created."
        logger.info(msg, extra={"email": data.email})
        http_exception.detail = msg
    except ValueError as e:
        logger.error(str(e), exc_info=False, extra={"email": data.email})
        http_exception.detail = str(e)
    except IntegrityError as e: # Fallback - for example the created id / email is the same
        logger.exception(str(e), exc_info=True, extra={"email": data.email})
        http_exception.detail = "Account could not be created in this time. Please try it later again."
    
    raise http_exception