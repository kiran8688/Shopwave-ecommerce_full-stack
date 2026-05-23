# app/db/init_db.py
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.db.seed_data import seed_data

async def init_db(db: AsyncSession) -> None:
    """
    Ensure the initial data exists in the database.
    Specifically checks if the first admin account exists and creates it if missing.
    If the admin user exists, verify they have the role 'admin', is_active=True,
    is_verified=True, and their password matches settings.FIRST_ADMIN_PASSWORD.
    If any check fails, update it and commit (self-healing bootstrap).
    """
    result = await db.execute(
        select(User).where(User.email == settings.FIRST_ADMIN_EMAIL)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        admin_user = User(
            email=settings.FIRST_ADMIN_EMAIL,
            username=settings.FIRST_ADMIN_USERNAME,
            hashed_password=hash_password(settings.FIRST_ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,
            full_name="System Admin"
        )
        db.add(admin_user)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            # This happens if another worker process created the user simultaneously
    else:
        # Self-healing: verify fields and credentials, update if necessary
        updated = False
        if user.role != "admin":
            user.role = "admin"
            updated = True
        if not user.is_active:
            user.is_active = True
            updated = True
        if not user.is_verified:
            user.is_verified = True
            updated = True
        if user.username != settings.FIRST_ADMIN_USERNAME:
            user.username = settings.FIRST_ADMIN_USERNAME
            updated = True
        if not verify_password(settings.FIRST_ADMIN_PASSWORD, user.hashed_password):
            user.hashed_password = hash_password(settings.FIRST_ADMIN_PASSWORD)
            updated = True

        if updated:
            try:
                await db.commit()
            except IntegrityError:
                await db.rollback()
    
    # NEW: Populate categories and products if empty
    await seed_data(db)
