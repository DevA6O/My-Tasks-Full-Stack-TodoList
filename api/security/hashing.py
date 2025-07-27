import re
import bcrypt

def hash_pwd(password: str) -> str:
    """ Hashes the password """
    if not isinstance(password, str):
        raise ValueError("Password must be a string.")

    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def is_hashed(password: str) -> bool:
    """ Checks if the password is in a valid hashed format. """
    if isinstance(password, str):
        return re.match(r'^\$2[aby]\$\d{2}\$[./A-Za-z0-9]{53}$', password) is not None
    
    return False