# app/services/auth_service.py
# Business logic for authentication — decoupled from HTTP layer.

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.core.security import verify_password, hash_password, needs_rehash


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Return the User if credentials are valid, else None."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    # Silently upgrade hash if parameters changed (e.g. Argon2 iteration count increased)
    if needs_rehash(user.hashed_password):
        user.hashed_password = hash_password(password)
        await db.commit()
    return user
