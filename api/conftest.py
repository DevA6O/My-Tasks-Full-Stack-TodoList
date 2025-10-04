import pytest_asyncio
from fastapi import Request
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple

from database.models import User, Todo
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
    return (created_user, db_session)


@pytest_asyncio.fixture
async def fake_todo(fake_user: Tuple[User, AsyncSession]) -> Tuple[Todo, User, AsyncSession]:
    # Define the fake user and the fake db session
    user, db_session = fake_user

    stmt = (
        insert(Todo).values(
            title="Valid title",
            description="Valid description",
            user_id=user.id
        )
        .returning(Todo)
    )
    result = await db_session.execute(stmt)
    await db_session.commit()

    # Check whether the todo is successfully created or not
    todo_obj = result.scalar_one_or_none()

    if todo_obj is None:
        raise ValueError("Fake todo could not be created.")
    
    await db_session.refresh(todo_obj)
    return (todo_obj, user, db_session)


# Define fake values for testing
user_agent = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
)
browser = "Mobile Safari"
device = "iPhone"
os_family = "iOS"
client_host = "000.111.222.333"
xForwarededFor = f"123.000.123.000, 999.000.999.000"


@pytest_asyncio.fixture
async def fake_request(fake_user: Tuple[User, AsyncSession]) -> Tuple[Request, User, AsyncSession]:
    """ Fixture to create a fake request """
    from unittest.mock import Mock

    mock_request = Mock(spec=Request)
    mock_request.headers = {
        "user-agent": user_agent,
        "x-forwarded-for": xForwarededFor
    }
    mock_request.client.host = client_host
    
    return (mock_request, fake_user[0], fake_user[1])



@pytest_asyncio.fixture
async def fake_refresh_token_with_session_id(
    fake_request: Tuple[Request, User, AsyncSession]
) -> Tuple[str, str, Request, User, AsyncSession]:
    """ Fixture to create a fake refresh token which contains a session id """
    from security.auth.refresh_token_service import RefreshTokenService
    from security.auth.jwt import decode_token

    mock_request, user, db_session = fake_request

    # Create the refresh token
    refresh_service = RefreshTokenService(
        request=mock_request,
        user_id=user.id,
        db_session=db_session
    )
    refresh_token: str = await refresh_service._create_and_store_refresh_token()

    # Decode the token to get the session id
    payload: dict = decode_token(token=refresh_token)
    session_id: str = str(payload.get("jti"))

    return (refresh_token, session_id, mock_request, user, db_session)