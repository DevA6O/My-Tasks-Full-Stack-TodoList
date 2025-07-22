import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from validation_models import LoginModel

class Login:
    def __init__(self, db_session: AsyncSession, data: LoginModel):
        self.db_session: AsyncSession = db_session
        self.data: LoginModel = data
    
    def verify_password(self, user_obj: User) -> bool:
        """ Verifies the password against the stored hash. """
        if not user_obj.password:
            return False
        
        return bcrypt.checkpw(self.data.password.encode("utf-8"), user_obj.password.encode("utf-8"))

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

        if not self.verify_password(user_obj=user):
            return None, "Incorrect password."

        return user, "Login successful."