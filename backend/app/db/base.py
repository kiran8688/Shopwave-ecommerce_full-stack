# app/db/base.py
# ─────────────────────────────────────────────────────────────────────────────
# Declarative base shared by every ORM model.
# Importing this module also imports all models so Alembic's autogenerate can
# detect new tables without explicit registration.
# ─────────────────────────────────────────────────────────────────────────────


from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    All ORM models inherit from this class.
    DeclarativeBase (SQLAlchemy 2.x) replaces the older declarative_base() call.
    It provides __tablename__ inference and type-annotated column support via
    Mapped[T] + mapped_column().
    """
    pass


# ── Import all models here so Alembic sees them ──────────────────────────────
# Alembic's env.py imports Base.metadata; it can only detect models that have
# already been imported into Python's module system.
from app.models import category, order, order_item, product, user  # noqa: F401, E402
