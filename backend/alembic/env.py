# alembic/env.py
# ─────────────────────────────────────────────────────────────────────────────
# Alembic migration environment.
# Configured for ASYNC migrations using asyncpg + SQLAlchemy 2.x.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import Base + all models so Alembic's autogenerate detects schema changes
from app.db.base import Base  # noqa: F401 — side-effect import registers all models
from app.core.config import settings

# Alembic Config object — provides access to values in alembic.ini
config = context.config

# Set the DATABASE_URL from application settings (overrides alembic.ini sqlalchemy.url)
# This ensures Docker env vars are respected at migration time.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret alembic.ini's logging config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata from our ORM models — used for autogenerate comparisons
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode — generates SQL script without a live DB connection.
    Useful for reviewing changes or deploying via DBA-approved scripts.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations synchronously within an async-acquired connection."""
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations.
    asyncpg is used for the async driver; NullPool is used because Alembic
    manages its own connection lifecycle and doesn't need pooling.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,    # No pooling — each migration run creates one connection
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online (live DB) migrations — called by Alembic CLI."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
