# app/services/product_service.py
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


async def get_product_by_id(db: AsyncSession, product_id: UUID) -> Product | None:
    result = await db.execute(select(Product).where(Product.id == product_id))
    return result.scalar_one_or_none()


async def get_product_by_sku(db: AsyncSession, sku: str) -> Product | None:
    result = await db.execute(select(Product).where(Product.sku == sku))
    return result.scalar_one_or_none()


async def decrement_stock(db: AsyncSession, product_id: UUID, qty: int) -> bool:
    """Atomically decrement stock. Returns False if insufficient stock."""
    product = await get_product_by_id(db, product_id)
    if not product or product.stock_quantity < qty:
        return False
    product.stock_quantity -= qty
    return True
