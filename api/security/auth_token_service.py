import logging
import uuid
from sqlalchemy import insert
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Insert
from fastapi import Request
from user_agents import parse
from pydantic import BaseModel
from database.models import Auth
from shared.decorators import validate_constructor

logger = logging.getLogger(__name__)

class AuthTokenDetails(BaseModel):
    user_id: uuid.UUID
    jti_id: uuid.UUID
    is_refresh_token: bool
    expires_at: int


class StoreAuthToken:
    @validate_constructor
    def __init__(self, request: Request, data: AuthTokenDetails, db_session: AsyncSession) -> None:
        # Validate the param
        if not isinstance(request, Request):
            raise ValueError("'request' be an instance of Request.")

        self.request: Request = request
        self.data: AuthTokenDetails = data
        self.db_session: AsyncSession = db_session

    def _get_ip_adress(self) -> str:
        """ Returns the ip address from user """
        x_forwarded_for: str | None = self.request.headers.get("x-forwarded-for")

        if x_forwarded_for:
            ip: str = x_forwarded_for.split(", ", [])[0].strip()
        else:
            ip: str = self.request.client.host

        return ip

    def _extract_informations(self, ip_address: str) -> Insert:
        """ Returns a SQLAlchemy Insert statement for inserting a record into the Auth table """
        # Extract user request informations
        user_agent_str = self.request.headers.get("user-agent", "")
        user_agent = parse(user_agent_str)

        # Define informations to save
        device = user_agent.device.family or "Unknown"
        browser = user_agent.browser.family or "Unknown"
        os_family = user_agent.os.family or "Unknown"

        # Create database statement
        stmt = (
            insert(Auth).values(
                jti_id=self.data.jti_id, 
                user_id=self.data.user_id,
                ip_address=ip_address, 
                user_agent=user_agent.ua_string,
                device=device, 
                browser=browser,
                os=os_family, 
                is_refresh_token=self.data.is_refresh_token,
                expires_at=self.data.expires_at
            )
            .returning(Auth.jti_id)
        )
        
        return stmt

    async def store_token(self) -> bool:
        """ Stores the auth token into the database """
        ip_address: str = self._get_ip_adress()

        try:
            # Store the token
            stmt = self._extract_informations(ip_address=ip_address)
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()

            # Check whether the insertion was successful
            jti_id = result.scalar_one_or_none()

            if jti_id:
                return True
        except IntegrityError as e:
            logger.exception(f"Insertion error: {str(e)}", exc_info=True, 
                extra={"ip_address": ip_address if 'ip_address' in locals() else 'unknown'})

        except SQLAlchemyError as e:
            logger.exception(f"Database error: {str(e)}", exc_info=True, 
                extra={"ip_address": ip_address if 'ip_address' in locals() else 'unknown'})

        return False