# app/db/init_db.py
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User
from app.db.seed_data import seed_data

async def init_db(db: AsyncSession) -> None:
    """
    Ensure the initial data exists in the database.
    Specifically checks if the first admin account exists and creates it if missing.
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
    
    # NEW: Populate categories and products if empty
    await seed_data(db)
