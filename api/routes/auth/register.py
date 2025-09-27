import logging
from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert, exists
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, EmailStr
from typing import Tuple

from database.models import User
from database.connection import get_db
from security.hashing import hash_pwd
from security.refresh_token_service import RefreshTokenService
from shared.decorators import validate_params

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_ERROR_MSG: str = "An unknown error occurred: Account could not be created. Please try again later."

class EmailAlreadyRegisteredException(Exception):
    """ A custom exception to handle it easier when
    the email is already registered """
    def __init__(self, message: str = "Registration failed: The email address is already registered.") -> None:
        self.message = message
        super().__init__(message)

class RegisterModel(BaseModel):
    username: str = Field(min_length=2, max_length=16)
    email: EmailStr
    password: str = Field(min_length=8, max_length=32)
    

class Register:
    @validate_params
    def __init__(self, db_session: AsyncSession, data: RegisterModel) -> None:
        self.db_session: AsyncSession = db_session
        self.data: RegisterModel = data

    async def _is_email_registered(self) -> bool:
        """ Check if the email address is already registered or not 
        
        Returns:
        ---------
            - A boolean
        """
        stmt = select(exists().where(User.email == self.data.email))
        result = await self.db_session.execute(stmt)
        return result.scalar()

    async def _insert_user_into_db(self) -> User | None:
        """ Helper-Method for the create_user method 
        This method is finally writing the user into the database

        Returns:
        ---------
            - (User): The user object or None
        """
        try:
            # Hashes the password
            hashed_pwd: str = hash_pwd(self.data.password)

            # Creates the user
            stmt = (
                insert(User).values(name=self.data.username, email=self.data.email, password=hashed_pwd)
                .returning(User.id)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()

            # Checks whether the user could successfully added
            user_id = result.scalar_one_or_none()

            if user_id:
                return await self.db_session.get(User, user_id)
        except ValueError as e:
            logger.exception(f"Password hashing failed: {str(e)}", exc_info=True, extra={"email": self.data.email})

        return None

    async def create_user(self) -> Tuple[User | None, str]:
        """ Create a new user account.

        Returns:
            A tuple containing:
                - The created User object (or None if creation failed)
                - A user-friendly status message
        """

        try:
            # Checks whether the email is already registered
            if await self._is_email_registered():
                log_msg: str = "Registration failed: Try to open an account with this email address, even though one already exists."
                
                logger.warning(log_msg, extra={"email": self.data.email})
                raise EmailAlreadyRegisteredException()
            
            # Creates the user
            user_obj = await self._insert_user_into_db()

            if user_obj:
                return user_obj, "Registration successful: Account successfully registered."
        except IntegrityError as e:
            logger.exception(f"Insertion failed: {str(e)}", exc_info=True, extra={"email": self.data.email})
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"email": self.data.email})

        # Return a default error message
        return None, DEFAULT_ERROR_MSG



@router.post("/register")
async def register_endpoint(request: Request, data: RegisterModel, db_session: AsyncSession = Depends(get_db)) -> JSONResponse:
    """ Endpoint to register a new user """
    try:
        # Default http exception
        http_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=DEFAULT_ERROR_MSG
        )

        # Creates the user with the specified information
        register_service = Register(db_session=db_session, data=data)
        user_obj, msg = await register_service.create_user()

        # Logs the creation message
        logger.info(str(msg), extra={"email": data.email})

        if user_obj:
            refresh_service = RefreshTokenService(
                request=request, user_id=user_obj.id, db_session=db_session, status_code=201
            )
            return await refresh_service.set_refresh_token()
    except EmailAlreadyRegisteredException as e:
        http_exception.status_code = status.HTTP_409_CONFLICT
        http_exception.detail = str(e)
    
    except ValueError as e:
        logger.exception(f"An unknown ValueError occurred: {str(e)}", exc_info=True, extra={"email": data.email})

    raise http_exception