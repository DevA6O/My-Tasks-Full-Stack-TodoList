import os
import jwt
import logging
import uuid
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException, status, APIRouter, Request, Response, Header
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from database.models import User
from database.connection import get_db

load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_bearer_token(authorization: str = Header(None)) -> str:
    """ Function to get the bearer token from header
    
    Returns:
    ---------
        - (str): A token in string format
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header."
        )
    return authorization[len("Bearer "):]


def decode_token(token: str) -> uuid.UUID:
    """ Function to decode the token 
    
    Returns:
    --------
        - (UUID): The user_id from token
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        # Check whether the user was found
        if user_id is None:
            raise ValueError("User could not be found.")
        
        # Return user id
        user_id = uuid.UUID(user_id)
        return user_id
    except PyJWTError as e:
        logger.exception(f"JWT verification failed: {str(e)}", exc_info=True)
        return None


def create_token(data: dict, expire_delta: timedelta | None = None) -> str:
    """ Creates an access or a refresh token 
    
    Returns:
    --------
        - (str): A token
    """
    if not data:
        raise ValueError("Data must not be empty.")
    
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary.")
    
    if not isinstance(expire_delta, (timedelta, type(None))):
        raise ValueError("Expire delta must be a timedelta or None.")
    
    # Create the token with expiration
    to_encode: dict = data.copy()
    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt




@router.post("/api/refresh_token/valid")
async def is_refresh_token_valid_endpoint(
    request: Request, response: Response, db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint which returns a access token if the user has a valid refresh token """
    refresh_token = request.cookies.get("refresh_token")

    # Validate the presence of the refresh token
    if not refresh_token:
        logger.warning("Refresh token missing in request to /api/refresh")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    
    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        # Check if the user ID is valid
        stmt = select(User).where(User.id == uuid.UUID(user_id))
        result_obj = await db_session.execute(stmt)
        result = result_obj.scalar_one_or_none()

        # If the user is not found, raise an error
        if user_id is None or result is None:
            logger.warning("User not found in database for refresh token", extra={"user_id": user_id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not be identified.")

        # Create a new access token
        access_token = create_token(data={"sub": user_id})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"access_token": access_token, "token_type": "bearer"})
    except PyJWTError:
        logger.exception("JWT verification failed for refresh token", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="This token is no longer valid.")
    
    except ValueError as e:
        logger.exception("Error in refresh token processing", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))