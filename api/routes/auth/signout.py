import jwt
import uuid
import logging
from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from security import SECRET_KEY, ALGORITHM
from security.jwt import get_bearer_token
from security.refresh_token_service import is_refresh_token_valid
from database.connection import get_db
from database.models import Auth

router = APIRouter()
logger = logging.getLogger(__name__)


# PROTOTYPE = NOT FOR FINAL USE!

@router.post("/api/signout")
async def signout_endpoint(
    request: Request, token: str = Depends(get_bearer_token),
    db_session: AsyncSession = Depends(get_db)
) -> None:
    """ Endpoint to logout an user """
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are not logged in."
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        jti_id: str = payload.get("jti")

        if not user_id or not jti_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You could not be identified."
            )

        if await is_refresh_token_valid(jti_id=uuid.UUID(jti_id), user_id=uuid.UUID(user_id), db_session=db_session):
            stmt = delete(Auth).where(
                Auth.user_id == uuid.UUID(user_id),
                Auth.jti_id == uuid.UUID(jti_id)
            )
            result = await db_session.execute(stmt)

            # Check whethter the deletion was successful
            deletion_obj = result.scalar_one_or_none()

            if deletion_obj:
                await db_session.commit()
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"message": "You have successfully logged out."}
                )
    except SQLAlchemyError as e:
        logger.exception(f"Database error: {str(e)}", exc_info=True)

    except ValueError as e:
        logger.exception(f"ValueError: {str(e)}", exc_info=True)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="An unexpected error occurred: Please try again later."
    )