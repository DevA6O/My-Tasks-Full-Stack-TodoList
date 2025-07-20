import os
import jwt
import logging
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, PyJWTError
from typing import Annotated
from passlib.context import CryptContext
from database.models import User
from database.connection import get_db

load_dotenv()

# NOTE: Maybe add a revoke session function 
# (with database management where the user can remove some session from his account, like Discord, Spotify, ...)

router = APIRouter()
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_token(data: dict, expire_delta: timedelta | None = None) -> str:
    """ Creates a access / refresh token """
    to_encode: dict = data.copy()
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def set_refresh_token(user_id: uuid.UUID, status_code: int = 200) -> JSONResponse:
    """ Set refresh token as HttpOnly cookie (no access_token returned) """
    refresh_token = create_token(data={"sub": str(user_id)}, expire_delta=timedelta(days=7))

    SECURE_HTTPS = os.getenv("SECURE_HTTPS", "False").lower() == "true"

    response = JSONResponse(status_code=status_code, content={})
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


@router.post("/api/refresh")
async def refresh_token(request: Request, response: Response, db_session: AsyncSession = Depends(get_db)):
    """ Checks whether a refresh token is valid and returns an access token if it is valid """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        logger.warning("Refresh token missing in request to /api/refresh")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result_obj = await db_session.execute(stmt)
        result = result_obj.scalar_one_or_none()

        if user_id is None or result is None:
            logger.warning("User not found in database for refresh token", extra={"user_id": user_id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not be identified.")

        access_token = create_token(data={"sub": user_id})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"access_token": access_token, "token_type": "bearer"})
    except PyJWTError:
        logger.warning("JWT verification failed for refresh token", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This token is no longer valid.")