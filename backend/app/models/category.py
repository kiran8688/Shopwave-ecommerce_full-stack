# app/models/category.py
# ─────────────────────────────────────────────────────────────────────────────
# Categories table — hierarchical (self-referential) via parent_id.
# Supports nested categories e.g. Electronics > Phones > Smartphones.
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(
        String(120), nullable=False, unique=True, index=True
        # Slug is the URL-safe version: "Smart Phones" → "smart-phones"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Self-referential FK for nested categories ─────────────────────────────
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        # SET NULL keeps orphaned subcategories visible rather than deleting them
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    parent: Mapped["Category | None"] = relationship(
        "Category", remote_side=[id], back_populates="children"
    )
    children: Mapped[list["Category"]] = relationship(
        "Category", back_populates="parent"
    )
    products: Mapped[list["Product"]] = relationship(   # type: ignore[name-defined]
        "Product", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<Category name={self.name}>"
