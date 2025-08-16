import bcrypt
import logging
from fastapi import HTTPException, status, APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from database.connection import get_db
from security.hashing import is_hashed
from security.refresh_token_service import RefreshTokenService
from shared.decorators import validate_constructor
from routes.auth.validation_models import LoginModel

logger = logging.getLogger(__name__)
router = APIRouter()

class Login:
    @validate_constructor
    def __init__(self, db_session: AsyncSession, data: LoginModel):     
        self.db_session: AsyncSession = db_session
        self.data: LoginModel = data
    
    def _verify_password(self, password_in_db: bytes) -> bool:
        """ Verifies the password against the stored hash. 
        The method compares the password with the method parameter 
        and the class instance from LoginModel.

        Returns:
        ---------
            - (bool): A boolean
        """
        # Checks whether the password in db is in bytes -> convert it in a string
        if isinstance(password_in_db, bytes):
            try:
                password_in_db_str = password_in_db.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Password in database is not UTF-8 decodable.")

        # Checks whether the password in db is a string, if not raise a ValueError
        elif isinstance(password_in_db, str):
            password_in_db_str = password_in_db
        else:
            raise ValueError("Password in database must be a string or bytes.")

        # Checks whether the password is not hashed -> raise ValueError
        if not is_hashed(password=password_in_db_str):
            raise ValueError("Password in database is not a valid hash format.")

        # Return the boolean whether the password is correct or not
        return bcrypt.checkpw(self.data.password.encode("utf-8"), password_in_db_str.encode("utf-8"))

    async def _get_user(self) -> User | None:
        """ Helper method: Tries to get the user from the database 
        using the provided credentials. 
        
        Returns:
        ---------
            - (User): The user object or None (if the user wasn't found)
        """
        stmt = select(User).where(User.email == self.data.email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self) -> Tuple[User | None, str]:
        """ Authenticate user with the provided credentials 
        
        Returns:
        ---------
            - (User): A user object or None (if the credentials are wrong)
            - (str): A detailed message 
        """
        try:
            user_obj = await self._get_user()

            # Checks whether the user could found with this email address
            if not user_obj:
                return None, "Login failed: This email address is not registered."
            
            # Checks whether the password, the user typed in, is not correct
            if not self._verify_password(password_in_db=user_obj.password):
                return None, "Login failed: Password is incorrect."

            return user_obj, "Login successful: Email address and password are correct."
        except SQLAlchemyError as e: # Fallback if the database has problems
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"email": self.data.email})
            return None, "Server error: An unexpected server error occurred. Please try again later."
    

@router.post("/api/login")
async def login_endpoint(request: Request, data: LoginModel, db_session: AsyncSession = Depends(get_db)) -> JSONResponse:
    """ Endpoint to log in a user """
    import logging
    try:
        # Default http exception
        http_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid login credentials."
        )

        # Define service and calling the authenticate method
        login_service = Login(db_session=db_session, data=data)
        user_obj, message = await login_service.authenticate()

        if user_obj: # Checks whether the credentials are correct
            refresh_service = RefreshTokenService(
                request=request, user_id=user_obj.id, db_session=db_session, status_code=200
            )
            response = await refresh_service.set_refresh_token()
            
            logging.info(response)
            logger.info("User logged in successfully.", extra={"email": data.email})
            return response
        
        # If the credentials are wrong
        logger.warning(f"Login failed: {message}", extra={"email": data.email})
    except ValueError as e: # Fallback
        logger.exception(str(e), exc_info=True)
    logging.info("Failed")
    raise http_exception