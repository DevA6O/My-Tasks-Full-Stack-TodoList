from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from inspect import signature

def validate_params(method):
    """ Validator to validate the db_session and / or the user_id """
    from functools import wraps

    @wraps(method)
    def wrapper(*args, **kwargs):
        # Bind positional args to parameter names
        sig = signature(method)
        bound_args = sig.bind_partial(*args, **kwargs)
        bound_args.apply_defaults()
        arguments = bound_args.arguments

        # Fetches the db_session and user_id
        db_session = arguments.get("db_session", None)
        user_id = arguments.get("user_id", None)

        if db_session is not None and not isinstance(db_session, AsyncSession):
            raise TypeError("db_session must be an instance of AsyncSession.")
        if user_id is not None and not isinstance(user_id, UUID):
            raise TypeError("user_id must be an instance of UUID.")
        
        return method(*args, **kwargs)
    
    return wrapper