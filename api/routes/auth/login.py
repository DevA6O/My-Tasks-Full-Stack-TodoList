import bcrypt
import logging
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
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
        self.db_session: AsyncSession = db_session
        self.data: LoginModel = data
    
    def verify_password(self, password_in_db: bytes) -> bool:
        """ Verifies the password against the stored hash. """
        if not isinstance(self.data.password, str):
            raise ValueError("Password must be a string.")
        
        if isinstance(password_in_db, bytes):
            try:
                password_in_db_str = password_in_db.decode("utf-8")
            except UnicodeDecodeError:
                raise ValueError("Password in database is not UTF-8 decodable.")

        elif isinstance(password_in_db, str):
            password_in_db_str = password_in_db
        else:
            raise ValueError("Password in database must be a string or bytes.")

        if not is_hashed(password=password_in_db_str):
            raise ValueError("Password in database is not a valid hash format.")

        return bcrypt.checkpw(self.data.password.encode("utf-8"), password_in_db_str.encode("utf-8"))

    async def _get_user(self):
        """ Helper method: Tries to get the user from the database using the provided credentials. """
        stmt = select(User).where(User.email == self.data.email)
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self):
        """ Authenticate user with the provided credentials. """
        user_obj = await self._get_user()

        if not user_obj:
            return None, "Email is not registered."

        if not self.verify_password(password_in_db=user_obj.password):
            return None, "Incorrect password."

        return user_obj, "Login successful."
    

@router.post("/api/login")
async def login(data: LoginModel, db_session: AsyncSession = Depends(get_db)):
    """ Endpoint to log in a user. """
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid login credentials."
    )

    try:
        login_service = Login(db_session=db_session, data=data)
        user_obj, message = await login_service.authenticate()

        if not user_obj:
            logger.warning(f"Login failed: {message}", extra={"email": data.email})
            raise http_exception
        
        response: JSONResponse = await set_refresh_token(user_id=user_obj.id, status_code=200)
        logger.info("User logged in successfully", extra={"email": data.email})
        return response
    except ValueError as e: # Fallback for any ValueError raised in the service
        logger.exception(str(e), exc_info=True)
        http_exception.detail = str(e)
        raise http_exception