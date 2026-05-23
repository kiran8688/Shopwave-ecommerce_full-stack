# app/models/order.py
# ─────────────────────────────────────────────────────────────────────────────
# Orders table — tracks a customer's purchase from cart → fulfilment.
# Status follows a strict state machine: pending → confirmed → shipped → delivered
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Owner ─────────────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,            # index=True speeds up "my orders" queries
    )

    # ── Status machine ────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        server_default="pending",
        index=True,
        # Valid statuses: pending | confirmed | processing | shipped | delivered | cancelled | refunded
    )

    # ── Financial totals ──────────────────────────────────────────────────────
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    shipping_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=0, server_default="0"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
        # total_amount = subtotal + tax_amount + shipping_amount (computed in service layer)
    )

    # ── Shipping address (denormalised snapshot) ──────────────────────────────
    # We snapshot the address at order time so changes to the user's profile
    # don't retroactively alter historical orders.
    shipping_name: Mapped[str] = mapped_column(String(150), nullable=False)
    shipping_address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_city: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_state: Mapped[str] = mapped_column(String(100), nullable=False)
    shipping_postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(2), nullable=False)   # ISO 3166-1 alpha-2

    # ── Payment ───────────────────────────────────────────────────────────────
    payment_intent_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, unique=True
        # Stripe / Razorpay payment intent — unique prevents duplicate charges
    )
    payment_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", server_default="pending"
        # pending | paid | failed | refunded
    )

    # ── Notes ─────────────────────────────────────────────────────────────────
    customer_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="orders")          # type: ignore
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Order id={self.id} status={self.status} total={self.total_amount}>"
