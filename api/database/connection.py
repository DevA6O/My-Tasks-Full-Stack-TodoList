import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from database.config import get_db_url

# Define global variables
logger = logging.getLogger(__name__)
DB_URL, TEST_MODE = get_db_url()


# Database connection setup
if not TEST_MODE:
    engine = create_async_engine(DB_URL, echo=False)
elif TEST_MODE:
    # (WARNING): Database engine ONLY for TESTS 
    from sqlalchemy.pool import StaticPool
    engine = create_async_engine(DB_URL, echo=False, connect_args={"check_same_thread": False}, poolclass=StaticPool)

async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def init_models():
    """ Initialize the database models """
    from database import models # import all models to create tables correctly

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def get_db():
    """ Dependency to get a database session """
    async with async_session() as session:
        try:
            if TEST_MODE:
                logger.info("Running in test mode, using in-memory database.")

            yield session
        finally:
            await session.close()