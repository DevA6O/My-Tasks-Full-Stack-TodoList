import logging
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select, insert, exists
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from database.connection import get_db
from .validation_models import RegisterModel
from security.jwt import set_refresh_token
from security.hashing import hash_pwd

router = APIRouter()
logger = logging.getLogger(__name__)

DEFAULT_ERROR_MSG: str = "An unknown error occurred: Account could not be created. Please try again later."

class Register:
    def __init__(self, db_session: AsyncSession, data: RegisterModel) -> None:
        # Validate the db session
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")

        self.db_session: AsyncSession = db_session
        self.data: RegisterModel = data

    async def is_email_registered(self) -> bool:
        """ Check if the email address is already registered or not 
        
        Returns:
        ---------
            - A boolean
        """
        stmt = select(
            exists().where(User.email == self.data.email)
        )
        result = await self.db_session.execute(stmt)
        return result.scalar()

    async def create_user(self) -> Tuple[User | None, str]:
        """ Create a new user account.

        Returns:
            A tuple containing:
                - The created User object (or None if creation failed)
                - A user-friendly status message
        """

        try:
            # Checks whether the email is registered
            if await self.is_email_registered():
                logger.warning(
                    "Try to open an account with this email address, even though one already exists.",
                    extra={"email": self.data.email}
                )
                return None, "This email address is already registered."
            
            # Hashes the password
            hashed_pwd: str = hash_pwd(self.data.password)

            # Creates the user
            stmt = (
                insert(User).values(
                    name=self.data.username, email=self.data.email, password=hashed_pwd
                ).returning(User.id)
            )
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()

            # Checks whether the user is successfully created
            user_id = result.scalar_one_or_none()

            if user_id is not None:
                user_obj = await self.db_session.get(User, user_id)
                return user_obj, "Account successfully registered."
        # Exception if the insertion was failed
        except IntegrityError as e:
            logger.exception(f"Insertion failed: {str(e)}", exc_info=True, extra={"email": self.data.email})
        
        # Exception if some database error occurred
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"email": self.data.email})

        # Return a standard error message to user
        return None, DEFAULT_ERROR_MSG



@router.post("/api/register")
async def register(data: RegisterModel, db_session: AsyncSession = Depends(get_db)) -> JSONResponse:
    """ Endpoint to register a new user """
    # Standard http exception
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=DEFAULT_ERROR_MSG
    )

    try:
        # Creates the user with the specified information
        register_service = Register(db_session=db_session, data=data)
        user_obj, msg = await register_service.create_user()

        # Checks whether the user was successfully registered
        if user_obj is not None:
            logger.info(str(msg), extra={"email": data.email})
            response: JSONResponse = await set_refresh_token(user_id=user_obj.id, status_code=201)
            return response
        
        logger.info(msg, extra={"email": data.email})
        http_exception.detail = msg
    except ValueError as e:
        logger.exception(f"An unknown ValueError occurred: {str(e)}", exc_info=True, extra={"email": data.email})

    raise http_exception