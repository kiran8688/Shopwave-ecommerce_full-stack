# app/main.py
# ─────────────────────────────────────────────────────────────────────────────
# Application entry point — creates the FastAPI app, registers middleware,
# mounts all routers, and defines lifespan events.
# ─────────────────────────────────────────────────────────────────────────────

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal


# ── Lifespan — runs once on startup / shutdown ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern FastAPI lifespan replaces the deprecated @app.on_event decorators.
    Code BEFORE 'yield' runs at startup; code AFTER runs at shutdown.
    """
    # Startup: warm the DB connection pool by issuing a no-op query
    print(f"STARTING: {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Bootstrap initial data (e.g., first admin user)
    async with AsyncSessionLocal() as db:
        await init_db(db)
        
    yield
    # Shutdown: close the async engine gracefully (releases DB connections)
    from app.db.session import engine
    await engine.dispose()
    print("STOPPED: Database connections closed.")


# ── Application factory ───────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",  # Hide schema in production if desired
    docs_url="/docs",          # Swagger UI
    redoc_url="/redoc",        # ReDoc UI
    lifespan=lifespan,
)


# ── CORS Middleware ───────────────────────────────────────────────────────────
# CORS must be registered BEFORE any route middleware so preflight OPTIONS
# requests are handled correctly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,    # Required for cookies (HttpOnly refresh token)
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers including Authorization
)

# ── Trusted Host Middleware ───────────────────────────────────────────────────
# Rejects requests with Host headers not in the allowed list — prevents
# HTTP Host header injection attacks.
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.ALLOWED_HOSTS,
    )


# ── Mount API router ──────────────────────────────────────────────────────────
# All routes live under /api/v1/... — this prefix is defined in settings.
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ── Root endpoint ────────────────────────────────────────────────────────────
@app.get("/", tags=["General"])
@app.head("/", tags=["General"])
async def root_ping() -> dict:
    """Root ping endpoint to verify API server is online."""
    return {
        "message": "Welcome to the ShopWave E-Commerce API",
        "docs_url": "/docs",
        "version": settings.APP_VERSION,
        "status": "healthy"
    }


# ── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Lightweight health endpoint used by Docker HEALTHCHECK and load balancers.
    Does NOT query the DB — that's a readiness check, not a liveness check.
    """
    return {"status": "ok", "version": settings.APP_VERSION}
