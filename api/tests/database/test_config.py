import os
import shutil
import importlib
import pytest
from pathlib import Path
from unittest.mock import patch
from pytest import MonkeyPatch, LogCaptureFixture
from database.config import move_test_database, get_db_url


def delete_test_db() -> bool:
    """ Deletes the test.db file and the test-dbs folder created in test mode """
    if os.path.exists("./test.db"):
        os.remove("./test.db")
    
    if os.path.exists("./test-dbs"):
        shutil.rmtree("./test-dbs")
    
    return True

class TestMoveTestDatabase:
    """ Test class for different test scenarios for move_test_database """
    
    def test_move_test_database_success(self) -> None:
        """ Tests the success case """
        # Create fake db
        with open("./test-success.db", "w") as file:
            file.write("")
        
        # Test the movement
        move_test_database("./test-success.db")
        
        # Check whether the file is in the test database folder
        path = Path("./test-dbs")
        files_db = list(path.glob("*.db"))
        assert len(files_db) == 1

        # Delete the created file and folder
        assert delete_test_db()

    def test_move_test_database_failed_no_test_db(self) -> None:
        """ Tests the failed case when no test.db file is exist """
        move_test_database("./test-failed.db")

        # Check that no folder has been created
        assert not os.path.exists("./test-dbs")


class TestGetDbURL:
    """ Test class for different test scenarios for get_db_url """

    def test_get_db_url_without_test_mode(self) -> None:
        """ Tests the case when test mode is not activated """
        db_url, test_mode = get_db_url()
        env_db_url: str = os.getenv("DATABASE_URL")

        assert not test_mode
        assert db_url == env_db_url

    def test_get_db_url_with_test_mode(self, monkeypatch: MonkeyPatch) -> None:
        """ Tests the case when test mode is activated """
        # Set TEST_MODE to true
        monkeypatch.setenv("TEST_MODE", "true")

        # Reload config
        import database.config as config
        importlib.reload(config)

        # Start check
        db_url, test_mode = get_db_url()
        env_db_url: str = os.getenv("DATABASE_URL")

        assert test_mode
        assert not db_url == env_db_url

    @pytest.mark.parametrize("input_value", [("y"), ("n")])
    def test_get_db_url_with_test_mode_and_secure_https(self, caplog: LogCaptureFixture, monkeypatch: MonkeyPatch, input_value: str) -> None:
        """ Tests the case when test mode and secure https is activated """
        monkeypatch.setenv("TEST_MODE", "true")
        monkeypatch.setenv("SECURE_HTTPS", "true")

        # Reload config
        import database.config as config
        importlib.reload(config)

        # Start check
        with patch("builtins.input", return_value=input_value):
            if input_value == "n":
                with pytest.raises(ValueError):
                    db_url, test_mode = get_db_url()
                    assert "Unable to run tests with secure HTTPS." in caplog.text
                return
            
            db_url, test_mode = get_db_url()
            env_db_url: str = os.getenv("DATABASE_URL")

            assert test_mode
            assert not db_url == env_db_url
            assert "Unable to run tests with secure HTTPS." in caplog.text