import pytest_asyncio
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User
from database.connection import engine, async_session


@pytest_asyncio.fixture
async def db_session():
    """ Fixture to provide a database session for tests. """
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = async_session(bind=conn, expire_on_commit=False)
        await conn.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()


# Fake user data for testing
from security.hashing import hash_pwd

fake_username: str = "FakeUser"
fake_email: str = "fake@email.com"
fake_password: str = "fakePassword123!"
fake_hashed_password: str = hash_pwd(fake_password)

@pytest_asyncio.fixture
async def fake_user(db_session: AsyncSession) -> Tuple[User, AsyncSession]:
    """ Fixture to create a fake user for testing purposes. """
    stmt = (
        insert(User).values(
            name=fake_username, 
            email=fake_email, 
            password=fake_hashed_password
        )
        .returning(User)
    )
    user_obj = await db_session.execute(stmt)
    await db_session.commit()

    # Return the created user and the database session
    created_user = user_obj.scalar_one_or_none()

    if created_user is None:
        raise ValueError("Failed to create a fake user in the fake database.")
    return created_user, db_session