from __future__ import annotations
import asyncio
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from backend.core.config import get_settings
from backend.core.database import Base

# Import models so they are registered on Base.metadata for autogenerate.
# backend.models.__init__ should import (or re-export) all model modules.
import backend.models  # noqa: F401


# Alembic Config object (from alembic.ini).
config = context.config

# Configure Python logging via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load DB URL from app settings (.env, environment variables, etc.)
settings = get_settings()
url = settings.DATABASE_URL

# Ensure Alembic uses the settings-based URL
config.set_main_option("sqlalchemy.url", url)

# Metadata used by "alembic revision --autogenerate"
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    In offline mode, Alembic does not create an engine/DBAPI connection.
    Instead, it emits SQL statements which can be reviewed or run manually.
    """
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def _do_run_migrations(connection) -> None:
    """Configure a live connection and run migrations."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    """Run migrations in 'online' mode using an async engine."""
    connectable = create_async_engine(url, poolclass=pool.NullPool)

    async with connectable.connect() as connection:
        # Alembic's migration runner is sync, so we bridge via run_sync().
        await connection.run_sync(_do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Online entry point (Alembic expects a sync function)."""
    asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()