from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from urllib.parse import urlparse

from app.config import DB_CONNECTION_STRING

# Parse the connection string
parsed_url = urlparse(DB_CONNECTION_STRING)

# Create async SQLAlchemy engine
engine = create_async_engine(
    f"postgresql+asyncpg://{parsed_url.username}:{parsed_url.password}@{parsed_url.hostname}{parsed_url.path}?ssl=require",
    echo=True
)

# Create async session factory
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# Async context manager for database sessions
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()