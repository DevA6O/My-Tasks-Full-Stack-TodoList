import os
import jwt
import logging
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from typing import Annotated
from passlib.context import CryptContext
from database.models import User
from database.connection import get_db

load_dotenv()

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_token(data: dict, expire_delta: timedelta | None = None):
    """ Creates a access / refresh token """
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def _fetch_user(user_id: uuid.UUID, db_session: AsyncSession = Depends(get_db)):
    """ Helper function for get_current_user to get the user from the database """
    stmt = select(User).where(User.email == user_id)
    result_obj = await db_session.execute(stmt)
    return result_obj.scalar_one_or_none()

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    """ Read the current user from the token """
    error_message: str = "Could not validate credentitals"

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=error_message,
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception
    except InvalidTokenError:
        logger.exception(error_message, exc_info=True)
        raise credentials_exception
    
    # Check if the user exists
    user_obj = await _fetch_user(user_id=user_id)

    if user_obj is None:
        raise credentials_exception

    return {"user_id": user_id, "username": user_obj.name}

async def add_token(user_id: uuid.UUID, status_code: int = 200):
    """ Create a refresh and access token """
    access_token = create_token(data={"sub": str(user_id)})
    refresh_token = create_token(data={"sub": str(user_id)}, expire_delta=timedelta(days=7))

    SECURE_HTTPS = os.getenv("SECURE_HTTPS", "False").lower() == "true"

    response = JSONResponse(
        status_code=status_code, 
        content={"access_token": access_token, "token_type": "bearer"}
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=SECURE_HTTPS,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/"
    )
    return response