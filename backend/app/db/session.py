# app/db/session.py
# ─────────────────────────────────────────────────────────────────────────────
# Async SQLAlchemy engine + session factory.
#
# ARCHITECTURE NOTE:
#   We use the fully async stack:
#     SQLAlchemy AsyncEngine  ←→  asyncpg driver  ←→  PostgreSQL 18
#
#   Each HTTP request gets its own AsyncSession (unit of work).
#   Sessions are injected via FastAPI's Depends() — see core/dependencies.py.
# ─────────────────────────────────────────────────────────────────────────────

import os
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,  # SQLAlchemy 2.x replacement for sessionmaker() in async contexts
    create_async_engine,
)

from app.core.config import settings

# Enable SSL for remote databases (e.g., hosted on Render or AWS)
connect_args = {}
is_remote_db = "localhost" not in settings.DATABASE_URL and "127.0.0.1" not in settings.DATABASE_URL
is_mock_mcp = os.getenv("MOCK_MCP") == "true"

if is_remote_db or is_mock_mcp:
    # Remote databases (like Render) often use self-signed certificates.
    # We bypass host and certificate verification to prevent ssl.SSLCertVerificationError.
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connect_args["ssl"] = ssl_context

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,         # Log all SQL to stdout when DEBUG=True — disable in production
    pool_size=10,                # Connections held open in the pool (tune to DB max_connections)
    max_overflow=20,             # Extra connections allowed beyond pool_size under peak load
    pool_pre_ping=True,          # Health-check connections before use
    connect_args=connect_args,
)

# ── Session factory ───────────────────────────────────────────────────────────
# async_sessionmaker is the 2.x-native async factory.
# expire_on_commit=False prevents SQLAlchemy from expiring ORM attributes after
# commit(), which would trigger extra SELECT queries when accessing the object
# again after the session closes — important in async code where you can't
# lazily load.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    FastAPI dependency — yields one AsyncSession per request.

    Usage in an endpoint:
        @router.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...

    The 'async with' block guarantees rollback on exception and session close
    even if the endpoint raises an unhandled error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit is done inside service layer — the session is just closed here
        except Exception:
            await session.rollback()   # Roll back on any unhandled exception
            raise
