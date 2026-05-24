# app/main.py
# ─────────────────────────────────────────────────────────────────────────────
# Application entry point — creates the FastAPI app, registers middleware,
# mounts all routers, and defines lifespan events.
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.init_db import init_db
from app.db.session import AsyncSessionLocal
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product


# ── Background task to release expired stock locks ─────────────────────────────
async def release_expired_locks() -> None:
    """
    Background task that queries for all pending, expired orders older than 30 minutes,
    restores product stock levels using pessimistic write locks, and cancels the orders.
    """
    while True:
        try:
            async with AsyncSessionLocal() as db:
                expiry_time = datetime.now(timezone.utc) - timedelta(minutes=30)
                query = select(Order).where(
                    Order.status == "pending",
                    Order.payment_status == "pending",
                    Order.created_at <= expiry_time
                )
                result = await db.execute(query)
                expired_orders = result.scalars().all()

                for order in expired_orders:
                    try:
                        # Explicitly query order items to avoid lazy load issues in async context
                        items_result = await db.execute(
                            select(OrderItem).where(OrderItem.order_id == order.id)
                        )
                        items = items_result.scalars().all()

                        # Retrieve and update each product with a pessimistic write lock (.with_for_update())
                        for item in items:
                            product_result = await db.execute(
                                select(Product).where(Product.id == item.product_id).with_for_update()
                            )
                            product = product_result.scalar_one_or_none()
                            if product:
                                product.stock_quantity += item.quantity

                        # Advance the order status to "cancelled" and payment status to "failed"
                        order.status = "cancelled"
                        order.payment_status = "failed"

                        await db.commit()
                        print(f"Released stock and cancelled expired pending order: {order.id}")
                    except Exception as e:
                        await db.rollback()
                        print(f"Error releasing locks for order {order.id}: {e}")
        except Exception as e:
            print(f"Error in release_expired_locks background loop: {e}")
        
        await asyncio.sleep(60)


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

    # Spin off the expired stock lock release loop as a background task
    task = asyncio.create_task(release_expired_locks())
        
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
    allow_origin_regex=r"https://.*\.onrender\.com|http://localhost(:\d+)?|http://127\.0.0\.1(:\d+)?",
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
