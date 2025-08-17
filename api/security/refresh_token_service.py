import uuid
import logging
import jwt
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request, Depends, HTTPException, status, APIRouter
from fastapi.responses import JSONResponse
from jwt.exceptions import PyJWTError

from security import REFRESH_MAX_AGE, ALGORITHM, SECRET_KEY, SECURE_HTTPS
from security.jwt import create_token
from security.auth_token_service import StoreAuthToken, AuthTokenDetails
from shared.decorators import validate_params
from database.models import Auth
from database.connection import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


class RefreshTokenService:
    @validate_params
    def __init__(
        self, 
        request: Request, user_id: uuid.UUID, db_session: AsyncSession, 
        status_code: int = 200, content: dict = None
    ):
        # Validate class params
        if not isinstance(request, Request):
            raise ValueError("'request' must be an instance of Request.")
        
        if not isinstance(status_code, int):
            raise ValueError("'status_code' must be an integer.")
        
        if not isinstance(content, dict) and content is not None:
            raise ValueError("'content' must be a dict.")
        
        self.request: Request = request
        self.user_id: uuid.UUID = user_id
        self.db_Session: AsyncSession = db_session
        self.status_code: int = status_code
        self.content: dict = content

    async def _create_and_store_refresh_token(self) -> str:
        """ Method which creates a refresh token and stores them 
        into the database 
        
        Returns:
        ---------
            - (str): Refresh token
        """
        # Create token
        jti_id: uuid.UUID = uuid.uuid4()
        refresh_token = create_token(
            data={
                "sub": str(self.user_id),
                "jti": str(jti_id)
            },
            expire_delta=timedelta(seconds=REFRESH_MAX_AGE)
        )

        # Store the token
        expires_at = int((datetime.now(timezone.utc) + timedelta(seconds=REFRESH_MAX_AGE)).timestamp())

        data = AuthTokenDetails(
            user_id=self.user_id, jti_id=jti_id, is_refresh_token=True,
            expires_at=expires_at
        )
        store_service = StoreAuthToken(request=self.request, data=data, db_session=self.db_Session)
        success = await store_service.store_token()

        # Check whether the storage was unsuccessful
        if not success:
            logger.warning("Failed to store the refresh token into the database.")
            return False

        return refresh_token
    
    async def set_refresh_token(self) -> JSONResponse:
        """ Set refresh token as HttpOnly cookie and store the refresh token
        into the database

        Returns:
        --------
            - (JSONResponse): A JSONResponse that has set the refresh token in the cookie
        """
        refresh_token = await self._create_and_store_refresh_token()

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication failed: An unknown error is occurred."
            )

        # Set the cookie in the response
        response = JSONResponse(status_code=self.status_code, content=self.content)
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=SECURE_HTTPS,
            samesite="lax",
            max_age=REFRESH_MAX_AGE,
            path="/"
        )
        return response
    


@validate_params # <- Error handler for user_id and db_session
async def is_refresh_token_valid(user_id: uuid.UUID, db_session: AsyncSession) -> bool:
    """ Helper-Function to check whether the refresh token is valid or invalid 
    
    Returns:
    ---------
        - A boolean
    """
    try:
        # Start database request to check the state of the token
        stmt = select(Auth).where(Auth.user_id == user_id)
        result = await db_session.execute(stmt)
        result_obj = result.scalar_one_or_none()

        # Check whether no token was found
        if result_obj is None:
            return False

        # Get values
        is_revoked = result_obj.revoked
        is_expired = result_obj.expires_at

        # Check whether the token is revoked or expired
        if is_revoked or (is_expired < datetime.now(timezone.utc).timestamp()):
            return False

        return True # <- Token is valid
    except SQLAlchemyError as e:
        logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"user_id": user_id})
        return False


@router.post("/api/refresh_token/valid")
async def is_refresh_token_valid_endpoint(
    request: Request, db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint which returns a access token if the user has a valid refresh token """
    refresh_token = request.cookies.get("refresh_token")

    # Validate the presence of the refresh token
    if not refresh_token:
        logger.warning("Refresh token missing in request.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")
    
    try:
        # Decode the refresh token
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        
        # Check whether sub exists
        if not user_id:
            logger.warning("User not found in database for refresh token", extra={"user_id": user_id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User could not be identified.")
        
        # Check whether the token is invalid
        if not await is_refresh_token_valid(user_id=user_id, db_session=db_session):
            logger.warning("Token is revoked or expired.", extra={"user_id": user_id})
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is invalid.")

        access_token = create_token(data={"sub": user_id})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"access_token": access_token, "token_type": "bearer"})
    except PyJWTError:
        logger.exception("JWT verification failed for refresh token", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token is no longer valid.")
    
    except ValueError as e:
        logger.exception("Error in refresh token processing", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))