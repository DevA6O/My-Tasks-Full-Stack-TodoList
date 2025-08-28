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
from security.jwt import create_token, decode_token
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
    


class RefreshTokenVerifier:
    @validate_params # <- Validator for db_session
    def __init__(self, request: Request, db_session: AsyncSession) -> None:
        # Validate param
        if not isinstance(request, Request):
            raise ValueError("request must be an instance of Request.")
        
        self.request: Request = request
        self.db_session: AsyncSession = db_session

        # Default http exception
        self.http_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        self.http_exception.detail = "Authorization failed: Authentication token could not be found."

    def _get_refresh_token(self) -> str:
        """ Returns the refresh_token
         
        Returns:
        --------
            - (str): The refresh token

        Raises:
        -------
        HTTPException
            If there is no refresh token in the cookie
        """
        refresh_token: str | None = self.request.cookies.get("refresh_token")

        if not refresh_token:
            raise self.http_exception
        
        return refresh_token

    @validate_params # <- Validator for user_id
    async def _check_token_in_db(self, user_id: uuid.UUID, jti_id: uuid.UUID) -> Auth | None:
        """ Check whether the token is in the database
         
        Returns:
        ---------
            - (Auth | None): An Auth object or None (if the token was not found in the database)  
        """
        # Validate param
        if not isinstance(jti_id, uuid.UUID):
            raise ValueError("jti_id must be an UUID.")

        # Database query
        stmt = select(Auth).where(
            Auth.user_id == user_id,
            Auth.jti_id == jti_id,
            Auth.revoked == False,
            Auth.expires_at > int(datetime.now(timezone.utc).timestamp())
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def is_valid(self) -> Auth:
        """ Validates whether the given refresh token is valid.

        Returns:
        --------
        bool
            The auth object

        Raises:
        -------
        HTTPException
            If the token is invalid, expired, or does not match the expected user/session.
        """
        refresh_token: str = self._get_refresh_token()
        payload: dict = decode_token(token=refresh_token)
        user_id: str = payload.get("sub")
        jti_id: str = payload.get("jti")

        try:
            # Check that the user_id or jti_id is not included in the payload
            if not user_id or not jti_id:
                self.http_exception.detail = "Authorization failed: Invalid token structure."
                raise self.http_exception

            # Get Auth object
            auth_obj: Auth | None = await self._check_token_in_db(
                user_id=uuid.UUID(user_id), jti_id=uuid.UUID(jti_id)
            )

            # Check whether the token could not be found
            if not auth_obj:
                logger.warning("Authorization failed: Refresh token is not in the database", extra={
                    "user_id": user_id, "jti_id": jti_id
                })
                raise self.http_exception
            
            return auth_obj
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True)
            self.http_exception.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        self.http_exception.detail = "Authorization failed: An unknown error has occurred. Please try again later."
        raise self.http_exception
        

        

@router.post("/api/token/refresh/valid")
async def is_refresh_token_valid_endpoint(
    request: Request, db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint which returns a access token if the user has a valid refresh token """
    try:
        verifier = RefreshTokenVerifier(request=request, db_session=db_session)
        auth_obj: Auth = await verifier.is_valid()

        access_token = create_token(data={"sub": str(auth_obj.user_id), "session_id": str(auth_obj.jti_id)})
        return JSONResponse(status_code=status.HTTP_200_OK, content={"access_token": access_token, "token_type": "bearer"})
    except PyJWTError:
        logger.exception("JWT verification failed for refresh token", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Authorization failed: Invalid token."
        )
    
    except ValueError as e:
        logger.exception(f"Error in refresh token processing: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Authorization failed: An unknown error occurred. Please try again later."
        )