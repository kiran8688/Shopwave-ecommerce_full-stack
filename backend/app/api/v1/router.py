# app/api/v1/router.py
# Aggregate all endpoint routers under a single APIRouter that main.py mounts.

from fastapi import APIRouter

from app.api.v1.endpoints import auth, categories, orders, payments, products, users, analytics

api_router = APIRouter()

# Each include_router call registers a sub-router with its own prefix and tags.
# Tags group endpoints in the /docs Swagger UI.
api_router.include_router(auth.router,       prefix="/auth",       tags=["Authentication"])
api_router.include_router(users.router,      prefix="/users",      tags=["Users"])
api_router.include_router(products.router,   prefix="/products",   tags=["Products"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(orders.router,     prefix="/orders",     tags=["Orders"])
api_router.include_router(payments.router,   prefix="/payments",   tags=["Payments"])
api_router.include_router(analytics.router,  prefix="/analytics",  tags=["Analytics"])
