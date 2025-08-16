import jwt
import logging
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext

from security import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

logger = logging.getLogger(__name__)

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