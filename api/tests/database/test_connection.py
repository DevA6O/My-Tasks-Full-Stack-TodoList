import pytest
import pytest_asyncio
from pytest import MonkeyPatch, LogCaptureFixture
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator, Any

from database.connection import engine, init_models, get_db, Base

class TestInitModels:
    """ Test class for database model initialization """

    @pytest_asyncio.fixture(autouse=True)
    async def reset_db(db_session: AsyncSession) -> None:
        """ Fixture to reset the database before each test """
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

            def check_tables(sync_conn):
                inspector = inspect(sync_conn)
                tables = inspector.get_table_names()
                assert tables == []

            await conn.run_sync(check_tables)

    @pytest.mark.asyncio
    async def test_init_models(self) -> None:
        """ Test if init_models creates the necessary tables """
        # Initialize models
        await init_models()

        # Check if the tables were created
        async with engine.begin() as conn:
            def check_tables(sync_conn):
                inspector = inspect(sync_conn)
                tables = inspector.get_table_names()

                assert "auth" in tables
                assert "users" in tables
                assert "todos" in tables
                assert len(tables) == 3

            await conn.run_sync(check_tables)


class TestGetDb:
    """ Test class for the get_db dependency """
    
    @pytest.fixture
    def setup_test_mode(self, monkeypatch: MonkeyPatch) -> None:
        """ Fixture to set the TEST_MODE in environment """
        def _enable_test_mode(mode: bool = False) -> None:
            if mode:
                monkeypatch.setenv("TEST_MODE", "true")
            elif not mode:
                monkeypatch.setenv("TEST_MODE", "false")

            # Reload the config and connection to apply the new environment variable
            import database.config as config
            import database.connection as connection
            import importlib

            importlib.reload(config)
            importlib.reload(connection)

            # Ensure TEST_MODE is set to True
            assert config.TEST_MODE == mode
        
        return _enable_test_mode
    

    async def assert_session(self) -> None:
        """ Helper function to assert session """
        # Get a database session from the dependency
        gen: AsyncGenerator = get_db()
        session: AsyncSession = await gen.__anext__()

        # Check if the session is valid
        assert session is not None
        assert isinstance(session, AsyncSession)

        assert session.is_active
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1

        # Close the session (trigger finally block)
        with pytest.raises(StopAsyncIteration):
            await gen.__anext__()

    def delete_test_db(self) -> bool:
        """ Deletes the test.db file and the test-dbs folder created in test mode """
        import os, shutil

        if os.path.exists("./test.db"):
            os.remove("./test.db")
        
        if os.path.exists("./test-dbs"):
            shutil.rmtree("./test-dbs")
        
        return True

    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_mode", [(True), (False)])
    async def test_get_db_success_with_different_modes(
        self, setup_test_mode: Any, caplog: LogCaptureFixture, test_mode: bool
    ) -> None:
        """ Test whether get_db works correctly, with TEST_MODE True, False and None """
        setup_test_mode(test_mode)

        # Check if the session is valid
        from database.connection import engine

        await self.assert_session()
        await engine.dispose() # Closes the engine 

        # Check if the log message is present
        if test_mode:
            assert "Running in test mode, using test database." in caplog.text
            assert self.delete_test_db()
        else:
            assert not "Running in test mode, using test database." in caplog.text