import bcrypt
import logging
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.connection import get_db
from routes.auth.validation_models import LoginModel
from security.hashing import is_hashed
from security.jwt import set_refresh_token

logger = logging.getLogger(__name__)
router = APIRouter()

class Login:
    def __init__(self, db_session: AsyncSession, data: LoginModel):
        # Validate the db session
        if not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an AsyncSession.")
                
        self.db_session: AsyncSession = db_session
        self.data: LoginModel = data
    
    def _verify_password(self, password_in_db: bytes) -> bool:
        """ Verifies the password against the stored hash. 
        The method compares the password with the method parameter 
        and the class instance from LoginModel.

        Returns:
        ---------
            - A boolean
        """
        if not isinstance(self.data.password, str):
            raise ValueError("Password must be a string.")
        
        # Checks whether the password in db is in bytes -> convert it in a string
        if isinstance(password_in_db, bytes):
            try:
                password_in_db_str = password_in_db.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Password in database is not UTF-8 decodable.")

        # Checks whether the password in db is a string, if not raise an ValueError
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
            - The user object or None (if the user wasn't found)
        """
        stmt = select(User).where(User.email == self.data.email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self) -> None:
        """ Authenticate user with the provided credentials. """
        try:
            # Gets the user object
            user_obj = await self._get_user()

            # Checks whether the user with the email exist or not
            if not user_obj:
                return None, "Email is not registered."
            
            # Checks whether the password, the user typed in, is correct or not
            if not self._verify_password(password_in_db=user_obj.password):
                return None, "Incorrect password."

            return user_obj, "Login successful."
        # Fallback if the database connection or something else is broken / invalid
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"email": self.data.email})
            return None, "Server error: An unexpected server error occurred. Please try again later."
    

@router.post("/api/login")
async def login(data: LoginModel, db_session: AsyncSession = Depends(get_db)) -> None:
    """ Endpoint to log in a user. """
    # Defines the standard http exception
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid login credentials."
    )

    try:
        # Defines the login service and calls the authenticate method
        login_service = Login(db_session=db_session, data=data)
        user_obj, message = await login_service.authenticate()

        # If the credentials or somethings else is wrong (e.g. database crash)
        if not user_obj:
            logger.warning(f"Login failed: {message}", extra={"email": data.email})
            raise http_exception
        
        # If the credentials are correct
        response: JSONResponse = await set_refresh_token(user_id=user_obj.id, status_code=200)
        logger.info("User logged in successfully", extra={"email": data.email})
        return response
    except ValueError as e: # Fallback for any ValueError raised in the service
        logger.exception(str(e), exc_info=True)
        http_exception.detail = str(e)
        raise http_exception