import logging
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from security.refresh_token_service import RefreshTokenVerifier
from database.connection import get_db
from database.models import Auth

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/api/signout")
async def signout_endpoint(request: Request, db_session: AsyncSession = Depends(get_db)) -> None:
    """ Endpoint to logout an user """    
    try:
        # Default http exception
        http_exception = HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

        # Verify the refresh token
        verifier = RefreshTokenVerifier(request=request, db_session=db_session)
        auth_obj: Auth = await verifier.is_valid()

        # Check whether the token is valid
        if auth_obj: # <- Security, in case something goes wrong, but not necessarily
            auth_obj.revoked = True
            await db_session.commit()

            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"message": "You have successfully logged out."}
            )
    except SQLAlchemyError as e:
        logger.exception(f"Database error: {str(e)}", exc_info=True)
        http_exception.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    except ValueError as e:
        logger.exception(f"ValueError: {str(e)}", exc_info=True)
    
    http_exception.detail = "Signout failed: An unexpected error occurred: Please try again later."
    raise http_exception