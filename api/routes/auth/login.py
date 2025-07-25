import re
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

    async def get_user(self):
        """ Tries to get the user from the database using the provided credentials. """
        stmt = select(User).where(
            User.email == self.data.email
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self):
        """ Authenticate user with the provided credentials. """
        user = await self.get_user()

        if not user:
            return None, "Email is not registered."

        if not self.verify_password(password_in_db=user.password):
            return None, "Incorrect password."

        return user, "Login successful."
    

@router.post("/login")
async def login(data: LoginModel, db_session: AsyncSession = Depends(get_db)):
    """ Endpoint to log in a user. """
    login_service = Login(db_session=db_session, data=data)
    user, message = await login_service.authenticate()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": message, "user_id": user.id, "username": user.username}
    )