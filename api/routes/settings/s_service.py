import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Tuple, Dict
from pydantic import BaseModel

from security.jwt import get_bearer_token, decode_token
from shared.decorators import validate_params
from database.connection import get_db
from database.models import User, Auth

router = APIRouter()
logger = logging.getLogger(__name__)

class SessionSchema(BaseModel):
    """ Perfect scheme for the sessions, with the most essential values """

    jti_id: UUID
    ip_address: str
    browser: str
    os: str

class SettingsService:
    @validate_params
    def __init__(self, payload: dict, db_session: AsyncSession) -> None:
        # Validate param
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict.")

        self.payload: dict = payload
        self.db_session: AsyncSession = db_session

        # Define values
        self.user_id_str: str = self.payload.get("sub")
        self.jti_id_str: str = self.payload.get("session_id")

        # Validate params
        if not self.user_id_str:
            raise ValueError("Authentication failed: Unknown user.")
        
        if not self.jti_id_str:
            raise ValueError("Authentication failed: Server could not verify the user.")
        
        # Define values with correct type
        self.user_id: UUID = UUID(self.user_id_str)


    async def _get_sessions(self) -> List[Dict[str, str]]:
        """ Helper-Method: Returns a list of sessions with the schema 'SessionSchema' 
        
        Returns:
        --------
            - A List contains:
                - A dictionary with active sessions
        """
        stmt = select(Auth).where(Auth.user_id == self.user_id, Auth.revoked == False)
        result = await self.db_session.execute(stmt)
        session_objs = result.scalars().all()

        return [
            {
                **SessionSchema.model_validate(session, from_attributes=True).model_dump(mode="json"),
                "current": str(session.jti_id) == str(self.jti_id_str)
            } 
            for session in session_objs
        ]

    
    async def _get_username_and_email(self) -> Tuple[str | None, str | None]:
        """ Helper-Method: Returns the username and email address 
        
        Returns:
        --------
            - A Tuple contains:
                - (str): Username
                - (str): Email address
        """
        stmt = select(User).where(User.id == self.user_id)
        result = await self.db_session.execute(stmt)
        user_obj: User = result.scalar_one_or_none()

        if user_obj:
            username: str = user_obj.name
            email: str = user_obj.email

            return username, email
        
        return None, None
    
    
    async def get(self) -> Dict[str, str | List]:
        """ Handler for user information
         
        Returns:
        --------
            - A Dictionary containing the following keys:
                - (str): Username
                - (email): Email address
                - (sessions): A list containing one or more dictionaries with different active sessions
        """
        try:
            sessions: List = await self._get_sessions()
            username, email = await self._get_username_and_email()

            return {
                "username": username,
                "email": email,
                "sessions": sessions
            }
        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, extra={"user_id": self.user_id})
            return {}


@router.post("/api/settings/service")
async def settings_service_endpoint(
    token: str = Depends(get_bearer_token), db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to get the user information and sessions """
    try:
        # Define default http exception
        http_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Loading failed: An unknown error has occurred. Please try again later."
        )

        # Decode token
        payload: dict = decode_token(token=token)

        # Get the informations
        service = SettingsService(payload=payload, db_session=db_session)
        informations = await service.get()

        if informations:
            return JSONResponse(status_code=status.HTTP_200_OK, content={"informations": informations})
    except TypeError as e:
        http_exception.detail = "Server error: A server error has occurred. Please try again later."
        http_exception.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        logger.exception(str(e), exc_info=True)

    except ValueError as e:
        http_exception.detail = str(e)
        logger.exception(str(e), exc_info=True)
    
    raise http_exception