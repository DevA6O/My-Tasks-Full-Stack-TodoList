import pytest_asyncio
from database.connection import engine, async_session


@pytest_asyncio.fixture
async def db_session():
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = async_session(bind=conn, expire_on_commit=False)
        await conn.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()