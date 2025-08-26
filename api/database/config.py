import os
import logging
from dotenv import load_dotenv
from typing import Tuple

load_dotenv()
logger = logging.getLogger(__name__)

TEST_MODE: bool = os.getenv("TEST_MODE", "false").lower() == "true"


# Move the old test database file
def move_test_database(TEST_DB: str) -> None:
    """ 
        Move the test databases to test-dbs
    """
    from pathlib import Path
    from datetime import datetime, timezone

    if os.path.exists(TEST_DB):
        source = Path(TEST_DB)
        target_dir = Path("./test-dbs")
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H-%M-%S")
        target = target_dir / f"test-{timestamp}.db"

        source.rename(target)


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
    TEST_DB: str = "./test.db"

    # Define the database URL based on environment variables
    if not TEST_MODE:
        DB_URL: str = os.getenv("DATABASE_URL")
        return DB_URL, False

    if TEST_MODE and SECURE_HTTPS:
        logger.warning("Unable to run tests with secure HTTPS.")
        confirm: str = input("[CRITICAL]: Do you want to run tests with secure HTTPS? (y/n): ")

        if confirm.lower() != "y":
            raise ValueError("Tests cannot run with secure HTTPS enabled. Please disable it or set TEST_MODE to false.")
    
    move_test_database(TEST_DB)
    return f"sqlite+aiosqlite:///{TEST_DB}", True