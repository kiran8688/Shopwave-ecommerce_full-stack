# app/core/dependencies.py
# ─────────────────────────────────────────────────────────────────────────────
# FastAPI dependency providers — injected via Depends() in route handlers.
# Centralising dependencies here means changing auth logic requires edits in
# only ONE place rather than every endpoint.
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# OAuth2PasswordBearer tells FastAPI where to find the Bearer token.
# tokenUrl is shown in the /docs UI "Authorize" dialog.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),      # Extract "Bearer <token>" from Authorization header
    db: AsyncSession = Depends(get_db),       # Inject database session
) -> User:
    """
    Decode the JWT, validate it, and return the matching User object.
    Raises HTTP 401 on any token problem.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},  # Required by RFC 6750
    )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except (ExpiredSignatureError, InvalidTokenError):
        raise credentials_exc

    # Load the user from the database — verify they still exist and are active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exc

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Convenience dependency — alias of get_current_user for readability."""
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Require admin role — use this dependency on admin-only endpoints.
    Returns HTTP 403 Forbidden (not 401) because the identity IS verified;
    they just lack permission.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions — admin role required",
        )
    return current_user
