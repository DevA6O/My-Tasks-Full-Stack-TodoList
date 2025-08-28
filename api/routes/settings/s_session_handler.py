import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from shared.decorators import validate_params
from database.connection import get_db
from database.models import Auth

router = APIRouter()
logger = logging.getLogger(__name__)

class SettingSessionsHandler:
    @validate_params
    def __init__(self, jti_id: UUID, db_session: AsyncSession) -> None:
        # Validate param
        if not isinstance(jti_id, UUID):
            raise TypeError("jti_id must be an UUID.")

        self.jti_id: UUID = jti_id
        self.db_session: AsyncSession = db_session

    async def revoke(self) -> bool:
        """ Invalidates the token """
        stmt = update(Auth).where(Auth.jti_id==self.jti_id).values(revoked=True)
        result = await self.db_session.execute(stmt)

        if result.rowcount > 0:
            await self.db_session.commit()
            return True
        
        return False


class SessionID(BaseModel):
    """ Validator for jti_id """

    jti_id: str


@router.post("/api/settings/session/revoke")
async def settings_revoke_session_endpoint(
    payload: SessionID, db_session: AsyncSession = Depends(get_db) 
) -> JSONResponse:
    try:
        handler = SettingSessionsHandler(jti_id=UUID(payload.jti_id), db_session=db_session)
        result = await handler.revoke()

        if result:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "The device has been successfully logged out."}
            )
    except TypeError as e:
        logger.exception(str(e), exc_info=True)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The device could not be logged out."
    )