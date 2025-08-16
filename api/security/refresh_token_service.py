import uuid
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request
from fastapi.responses import JSONResponse

from security.jwt import create_token
from security.auth_token_service import StoreAuthToken, AuthTokenDetails
from shared.decorators import validate_constructor

logger = logging.getLogger(__name__)
load_dotenv()

REFRESH_MAX_AGE = int(os.getenv("REFRESH_MAX_AGE", 60 * 60 * 24 * 7))  # Default to 7 days

class RefreshTokenService:
    @validate_constructor
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

        # Secure HTTPS setting
        SECURE_HTTPS = os.getenv("SECURE_HTTPS", "False").lower() == "true"

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