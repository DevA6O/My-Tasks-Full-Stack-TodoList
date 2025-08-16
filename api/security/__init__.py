import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_MAX_AGE = int(os.getenv("REFRESH_MAX_AGE", 60 * 60 * 24 * 7))  # Default to 7 days
SECURE_HTTPS = os.getenv("SECURE_HTTPS", "False").lower() == "true"