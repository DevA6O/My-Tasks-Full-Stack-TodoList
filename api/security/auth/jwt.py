import jwt
import logging
from uuid import UUID
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Header, Depends
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Auth
from database.connection import get_db
from security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def decode_token(token: str) -> dict:
    """ Function to decode the token 
    
    Returns:
    --------
        - (dict): The payload or an empty dict
    """
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except PyJWTError as e:
        logger.exception(f"JWT verification failed: {str(e)}", exc_info=True)
    
    return {}


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



async def _verify_bearer_token(token: str, db_session: AsyncSession) -> bool:
    """ Helper-Function for get_bearer_token to validate the correctness of the token """
    payload: dict = decode_token(token=token)
    session_id: str = payload.get("session_id")

    if not session_id:
        raise TypeError("Authentication failed: Server could not verify the user.")

    # Start checking 
    stmt = select(Auth).where(Auth.jti_id == UUID(session_id), Auth.revoked == False)
    result = await db_session.execute(stmt)
    return bool(result.scalar_one_or_none())


async def get_bearer_token(authorization: str = Header(None), db_session: AsyncSession = Depends(get_db)) -> str:
    """ Function to get the bearer token from header
    
    Returns:
    ---------
        - (str): A token in string format
    """
    try:
        http_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed: An unknown error is occurred. Please try again later."
        )

        # Verify the access token
        if authorization and authorization.startswith("Bearer "):
            token: str = authorization[len("Bearer "):]

            if await _verify_bearer_token(token=token, db_session=db_session):
                return token
        
        raise http_exception
    except (TypeError, Exception) as e:
        logger.exception(f"An unexpected error is occurred: {str(e)}", exc_info=True)

    raise http_exception