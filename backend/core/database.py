from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    pass


@lru_cache
def get_async_engine():
    """
    Return a singleton async SQLAlchemy engine.
    Cached so we don't create multiple engines/pools.
    """
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set. Add it to your .env.")
    # echo=False by default; flip to True while debugging SQL
    return create_async_engine(db_url, echo=False, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Return a singleton async session factory.
    """
    return async_sessionmaker(bind=get_async_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yields an AsyncSession and cleans it up.
    Usage:
        async def route(session: AsyncSession = Depends(get_session)):
    """
    async_session = get_session_factory()
    async with async_session() as session:
        yield session


# Optional: handy alias for tests/fixtures
async_session_maker = get_session_factory()