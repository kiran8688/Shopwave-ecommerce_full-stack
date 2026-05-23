# app/models/user.py
# ─────────────────────────────────────────────────────────────────────────────
# Users table — stores credentials, profile data, and role.
# UUID primary key prevents enumeration attacks (vs sequential integers).
# ─────────────────────────────────────────────────────────────────────────────

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    # ── Primary key ───────────────────────────────────────────────────────────
    # server_default=func.gen_random_uuid() delegates UUID generation to PG 18
    # so inserts without an explicit id still get a valid UUID.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
        # index=True speeds up login lookups (WHERE email = ?)
    )
    username: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    full_name: Mapped[str | None] = mapped_column(String(150), nullable=True)

    # ── Security ──────────────────────────────────────────────────────────────
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    # Argon2 hashes are ~95 chars; 255 gives headroom for future algorithm changes

    # ── Access control ────────────────────────────────────────────────────────
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default="customer", server_default="customer"
        # Roles: "customer" | "admin" — extend with PG ENUM if more roles needed
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
        # Email verification status — verified users can checkout
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),   # PG sets this on INSERT — no Python datetime needed
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),         # SQLAlchemy triggers this on UPDATE
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    orders: Mapped[list["Order"]] = relationship(   # type: ignore[name-defined]
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",   # Deleting a user cascades to their orders
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email}>"
