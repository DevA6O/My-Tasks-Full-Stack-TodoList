import os
import logging
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()
logger = logging.getLogger(__name__)

TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"

# Get the database URL
def get_db_url() -> Tuple[str, bool]:
    """
        Get the suitable database URL based on environment variables.

        Returns:
        --------
            Tuple[str, bool]: A tuple containing the database URL and a boolean indicating if it's a test mode.

        Raises:
        -------
            ValueError: If the database URL cannot be set up correctly for test mode with secure HTTPS. 
    """
    SECURE_HTTPS: bool = os.getenv("SECURE_HTTPS", "false").lower() == "true"

    # Define the database URL based on environment variables
    if not TEST_MODE:
        DB_URL: str = os.getenv("DATABASE_URL")
        return DB_URL, False

    if TEST_MODE and SECURE_HTTPS:
        logger.warning("Unable to run tests with secure HTTPS.")
        confirm: str = input("[CRITICAL]: Do you want to run tests with secure HTTPS? (y/n): ")

        if confirm.lower() != "y":
            raise ValueError("Tests cannot run with secure HTTPS enabled. Please disable it or set TEST_MODE to false.")
    
    return "sqlite+aiosqlite:///:memory:", True