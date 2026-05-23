# app/models/product.py
# ─────────────────────────────────────────────────────────────────────────────
# Products table — core catalogue entity.
# Uses NUMERIC for price to avoid floating-point rounding errors in money math.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    slug: Mapped[str] = mapped_column(
        String(220), nullable=False, unique=True, index=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sku: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True
        # Stock Keeping Unit — internal product code, must be unique
    )

    # ── Pricing ───────────────────────────────────────────────────────────────
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
        # Numeric(10, 2): up to 99,999,999.99 — precise decimal storage, no float errors
    )
    compare_at_price: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True
        # "Was" price — shown crossed-out when product is on sale
    )

    # ── Inventory ─────────────────────────────────────────────────────────────
    stock_quantity: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
        # Soft-delete flag — inactive products hidden from storefront but kept in DB
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )

    # ── Media ─────────────────────────────────────────────────────────────────
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    thumbnail_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Category FK ───────────────────────────────────────────────────────────
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,                  # index=True speeds up category-filtered product listings
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    category: Mapped["Category"] = relationship("Category", back_populates="products")  # type: ignore
    order_items: Mapped[list["OrderItem"]] = relationship(  # type: ignore[name-defined]
        "OrderItem", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product sku={self.sku} name={self.name}>"
