from __future__ import annotations
from logging.config import fileConfig
from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from backend.core.config import get_settings
from backend.core.database import Base
try:
    import backend.models 
except Exception:
    pass

# Alembic Config object
config = context.config

# Configure Python logging via alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Load DB URL from .env via app settings
settings = get_settings()
url = settings.DATABASE_URL  

# Ensure Alembic uses this URL
config.set_main_option("sqlalchemy.url", url)

# Target metadata for 'alembic revision autogenerate'
# Autogenerate inspects this metadata for changes.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    - No engine/DBAPI is created; It just shows the SQL statements so we can 
    run them manually against a database.
    - Useful for generating migration scripts without connecting to the DB.
    """
    context.configure(
        url=url,  # use the settings-based URL
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,             # detect type changes
        compare_server_default=True,   # detect server default changes
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
    """Run migrations in 'online' mode with an **async** engine."""
    connectable = create_async_engine(url, poolclass=pool.NullPool)
    async with connectable.connect() as connection:
        # bridge to sync migration API
        await connection.run_sync(_do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online runs (wraps the async coroutine as Alembic needs
    a synchronous entry point to run)."""
    import asyncio
    asyncio.run(run_migrations_online_async())


# --- Choose offline vs online path
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()