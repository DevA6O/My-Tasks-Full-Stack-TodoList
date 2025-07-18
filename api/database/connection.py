import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DB_URL: str = os.getenv("DATABASE_URL")

engine = create_async_engine(DB_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def init_models():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

# For FastAPI Depends
async def get_db():
    async with async_session() as session:
        yield session