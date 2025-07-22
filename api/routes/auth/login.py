import bcrypt
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.connection import get_db
from routes.auth.validation_models import LoginModel

router = APIRouter()

class Login:
    def __init__(self, db_session: AsyncSession, data: LoginModel):
        self.db_session: AsyncSession = db_session
        self.data: LoginModel = data
    
    def verify_password(self, password_in_db: bytes) -> bool:
        """ Verifies the password against the stored hash. """
        if isinstance(password_in_db, str):
            password_in_db = password_in_db.encode("utf-8")

        if not isinstance(password_in_db, bytes):
            raise ValueError("Password in database is not in bytes or string format.")

        if not password_in_db:
            return False
        
        return bcrypt.checkpw(self.data.password.encode("utf-8"), password_in_db)

    async def get_user(self):
        """ Tries to get the user from the database using the provided credentials. """
        stmt = select(User).where(
            User.email == self.data.email
        )
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()

    async def authenticate(self):
        """ Authenticate user with the provided credentials. """
        user = await self.get_user()

        if not user:
            return None, "Email is not registered."

        if not self.verify_password(password_in_db=user.password):
            return None, "Incorrect password."

        return user, "Login successful."
    

@router.post("/login")
async def login(data: LoginModel, db_session: AsyncSession = Depends(get_db)):
    """ Endpoint to log in a user. """
    login_service = Login(db_session=db_session, data=data)
    user, message = await login_service.authenticate()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message
        )
    
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": message, "user_id": user.id, "username": user.username}
    )