import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Tuple
from pydantic import BaseModel

from security.jwt import get_bearer_token, decode_token
from shared.decorators import validate_params
from database.connection import get_db
from database.models import User, Auth

router = APIRouter()
logger = logging.getLogger(__name__)

class SettingsService:
    @validate_params
    def __init__(self, user_id: UUID, db_session: AsyncSession) -> None:
        self.user_id: UUID = user_id
        self.db_session: AsyncSession = db_session

    async def _get_sessions(self) -> List:
        """ Returns all active sessions """
        stmt = select(Auth).where(Auth.user_id == self.user_id)
        result = await self.db_session.execute(stmt)
        return result.scalars().all()
    
    async def _get_username_and_email(self) -> Tuple[str, str]:
        """ Returns username and email """
        stmt = select(User).where(User.id == self.user_id)
        result = await self.db_session.execute(stmt)
        user_obj: User = result.scalar_one_or_none()

        if user_obj:
            username: str = user_obj.name
            email: str = user_obj.email

            return username, email
        
        return None, None
    
    async def get(self) -> dict:
        """ Returns user information and sessions """
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


class SessionSchema(BaseModel):
    jti_id: UUID
    ip_address: str
    browser: str
    os: str

    class Config:
        from_attributes = True 


@router.post("/api/settings/service")
async def settings_service(
    token: str = Depends(get_bearer_token), db_session: AsyncSession = Depends(get_db)
) -> JSONResponse:
    """ Endpoint to get the user information and sessions """
    try:
        http_exception = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fetch failed: Information about the user could not be found. Please try again later."
        )

        payload: dict = decode_token(token=token)
        user_id_str: str = payload.get("sub")
        
        if not user_id_str:
            raise ValueError("Token error: User ID is not included in the token.")
        
        service = SettingsService(user_id=UUID(user_id_str), db_session=db_session)
        informations = await service.get()

        if informations:
            return JSONResponse(
                status_code=status.HTTP_200_OK, 
                content={
                    "message": "Fetch successful: Information about the user could be found.",
                    "informations": {
                        "username": informations["username"],
                        "email": informations["email"],
                        "sessions": [session.model_dump(mode="json") for session in map(SessionSchema.model_validate, informations["sessions"])]
                    }
                }
            )
    except Exception:
        logger.exception("Fetch failed: An unexpected error is occurred.", exc_info=True)
    
    raise http_exception