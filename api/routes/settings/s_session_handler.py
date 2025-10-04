import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from security.auth.jwt import get_bearer_token, decode_token
from shared.decorators import validate_params
from database.connection import get_db
from database.models import Auth

router = APIRouter()
logger = logging.getLogger(__name__)

class SettingSessionsHandler:
    @validate_params
    def __init__(self, jti_id: UUID, current_token: str, db_session: AsyncSession) -> None:
        # Validate params
        if not isinstance(jti_id, UUID):
            raise TypeError("jti_id must be an UUID.")
        
        if not isinstance(current_token, str):
            raise TypeError("current_token must be a string.")

        self.jti_id: UUID = jti_id
        self.token: str = current_token
        self.db_session: AsyncSession = db_session

        self.session_id: str | None = None
        self.user_id: str | None = None

        # Decode the token
        self.__decode_token()

    def __decode_token(self) -> None:
        """ Decode the token and set the session_id and user_id globally """
        payload: dict = decode_token(token=self.token)
        
        # Check whether the token could not be decoded correclty
        if not payload:
            raise ValueError("Invalid token: Token has no payload.")

        # Extract the session id and the user id from the token
        self.session_id: str = payload.get("session_id", None)
        self.user_id: str = payload.get("sub", None)

        # Check whether the values are in the token
        if not self.session_id:
            raise ValueError("session_id must be not None.")
        
        if not self.user_id:
            raise ValueError("sub must be not None.")
        
        # Try to convert the user_id to a UUID
        self.user_id: UUID = UUID(self.user_id)


    async def revoke(self) -> bool:
        """ Invalidates the token 
        
        Returns:
        --------
            - A boolean
        """
        # Check whether the session is connected with the current session
        # if self._is_session_match():
        if str(self.jti_id) == str(self.session_id):
            logger.warning(
                "User tried to revoke the current session", extra={
                    "user_id": self.user_id,
                    "jti_id": self.jti_id,
                    "token": self.token
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="You cannot end the current session yourself. Please log out instead."
            )

        # Update the session as revoked
        stmt = (update(Auth)
            .where(
                Auth.jti_id == self.jti_id,
                Auth.user_id == self.user_id
            ).values(revoked=True)
        )
        result = await self.db_session.execute(stmt)

        # Check whether the update was unsuccessful
        if not result.rowcount > 0:
            logger.warning(
                "Update failed: The session could not be revoked successfully due to an " \
                "unexpected update error.", extra={
                    "user_id": self.user_id,
                    "jti_id": self.jti_id,
                    "token": self.token,
                }
            )
            return False, self.user_id

        # If the update was successful
        await self.db_session.commit()
        return True, self.user_id



class SessionID(BaseModel):
    """ Validator for jti_id """

    jti_id: str


@router.post("/session/revoke")
async def settings_revoke_session_endpoint(
    payload: SessionID, token: str = Depends(get_bearer_token), db_session: AsyncSession = Depends(get_db) 
) -> JSONResponse:
    """ """
    http_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="The device could not be logged out."
    )

    try:
        handler = SettingSessionsHandler(jti_id=UUID(payload.jti_id), current_token=token, db_session=db_session)
        result, user_id = await handler.revoke()

        if not result:
            # logging occurs via revoke method
            raise http_exception

        # If it was successful
        logger.info(
            "Device successfully logged out.", extra={
                "user_id": user_id,
                "jti_id": payload.jti_id,
                "token": token
            }
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "The device has been successfully logged out."}
        )
    except (TypeError, ValueError) as e:
        logger.exception(str(e), exc_info=True)
        raise http_exception