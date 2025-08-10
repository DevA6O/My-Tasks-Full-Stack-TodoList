from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

def validate_constructor(method):
    """ Validator to validate the db_session and / or the user_id """
    from functools import wraps

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        # Fetches the db_session and user_id
        db_session = kwargs.get("db_session", None)
        user_id = kwargs.get("user_id", None)

        if db_session is not None and not isinstance(db_session, AsyncSession):
            raise ValueError("db_session must be an instance of AsyncSession.")
        if user_id is not None and not isinstance(user_id, UUID):
            raise ValueError("user_id must be an instance of UUID.")
        
        return method(self, *args, **kwargs)
    
    return wrapper