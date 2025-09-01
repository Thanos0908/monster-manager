from functools import lru_cache
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.core.config import get_settings
from sqlalchemy import MetaData

# Global naming conversion for cleaner migrations with Alembic. It avoids the auto-naming of contstarins and indexes and helps Alembic when comparing 
# models to the DB. That way there are no unstable names that lead to noisy “rename constraint” operations—even if nothing meaningful changed.
# A global naming convention makes names predictable and consistent, so migrations are cleaner and diffs are deterministic.
metadata = MetaData(naming_convention={
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_N_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
    metadata = metadata


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