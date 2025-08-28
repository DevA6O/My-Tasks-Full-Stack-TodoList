import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database.connection import get_db
from database.models import Auth

router = APIRouter()
logger = logging.getLogger(__name__)

class SettingSessionsHandler:
    def __init__(self, jti_id: UUID, db_session: AsyncSession) -> None:
        # self.user_id: UUID = user_id
        self.jti_id: UUID = jti_id
        self.db_session: AsyncSession = db_session

    async def revoke(self) -> None:
        """ """
        stmt = delete(Auth).where(Auth.jti_id==self.jti_id)
        result = await self.db_session.execute(stmt)

        if result.rowcount > 0:
            await self.db_session.commit()
            return True
        return False


class SessionID(BaseModel):
    jti_id: str

@router.post("/api/settings/session/revoke")
async def settings_revoke_session_endpoint(
    payload: SessionID, db_session: AsyncSession = Depends(get_db) 
) -> JSONResponse:
    logger.info(payload.jti_id)
    handler = SettingSessionsHandler(jti_id=UUID(payload.jti_id), db_session=db_session)
    await handler.revoke()
    return JSONResponse(content="Success")