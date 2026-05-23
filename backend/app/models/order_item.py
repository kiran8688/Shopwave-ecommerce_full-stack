# app/models/order_item.py
# ─────────────────────────────────────────────────────────────────────────────
# OrderItems table — the line items inside an order.
# Price is snapshotted at order creation so future price changes don't corrupt
# historical order values.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    order_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        # RESTRICT prevents deleting products that appear in any order
        nullable=False,
        index=True,
    )

    # ── Snapshot data — frozen at order creation time ─────────────────────────
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    product_sku: Mapped[str] = mapped_column(String(100), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
        # Copied from product.price at checkout — future price changes don't alter this
    )

    # ── Line totals ───────────────────────────────────────────────────────────
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
        # line_total = unit_price * quantity (computed in service layer before insert)
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    order: Mapped["Order"] = relationship("Order", back_populates="items")    # type: ignore
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")  # type: ignore

    def __repr__(self) -> str:
        return f"<OrderItem product={self.product_name} qty={self.quantity}>"
