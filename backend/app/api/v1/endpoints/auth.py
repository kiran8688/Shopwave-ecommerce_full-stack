# app/api/v1/endpoints/auth.py
# ─────────────────────────────────────────────────────────────────────────────
# Authentication endpoints:
#   POST /auth/register   — create account
#   POST /auth/login      — obtain access + refresh tokens
#   POST /auth/refresh    — exchange refresh token for a new access token
#   POST /auth/logout     — clear the refresh token cookie
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.mcp import notify_mcp, analytics_mcp

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserRegisterRequest

router = APIRouter()

# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    body: UserRegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    Create a new user account.
    Returns access token in body and sets refresh token as HttpOnly cookie.
    """
    # Check for duplicate email
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password before storing — plain text NEVER touches the database
    user = User(
        email=body.email,
        username=body.username,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)    # Reload the row to get server-generated id, timestamps

    # ── MCP Integration: Send Welcome Email & Log Analytics ───────────────────
    # We call these mocked MCPs as background-like tasks or synchronously 
    await notify_mcp.call_tool(
        "send_email",
        to_email=user.email,
        subject="Welcome to ShopWave!",
        body=f"Hi {user.username or user.email}, your account was successfully created."
    )
    await analytics_mcp.call_tool(
        "log_event",
        event_name="user_registered",
        payload={"user_id": str(user.id), "email": user.email}
    )
    # ──────────────────────────────────────────────────────────────────────────

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    # Store refresh token in HttpOnly cookie — JS cannot read it, preventing XSS theft
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,           # HTTPS only — set False for local dev
        samesite="lax",        # Protects against CSRF while allowing top-level navigation
        max_age=60 * 60 * 24 * 7,   # 7 days in seconds
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),   # FastAPI parses username + password fields
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """
    OAuth2 password flow — returns access token; sets refresh token cookie.
    Uses 'username' field for the email address (OAuth2 spec requirement).
    """
    from app.services.auth_service import authenticate_user
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account deactivated")

    # ── MCP Integration: Log Login Event ──────────────────────────────────────
    await analytics_mcp.call_tool(
        "log_event",
        event_name="user_login",
        payload={"user_id": str(user.id), "email": user.email}
    )
    # ──────────────────────────────────────────────────────────────────────────

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))

    response.set_cookie("refresh_token", refresh_token, httponly=True, secure=True, samesite="lax", max_age=604800)

    return TokenResponse(access_token=access_token, token_type="bearer")


# ── Refresh ───────────────────────────────────────────────────────────────────
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Issue a new access token using a valid refresh token."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found in cookies")
    from jwt.exceptions import InvalidTokenError
    try:
        payload = decode_refresh_token(refresh_token)
        user_id = payload["sub"]
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    new_access = create_access_token(str(user.id))
    new_refresh = create_refresh_token(str(user.id))
    response.set_cookie("refresh_token", new_refresh, httponly=True, secure=True, samesite="lax", max_age=604800)

    return TokenResponse(access_token=new_access, token_type="bearer")


# ── Logout ────────────────────────────────────────────────────────────────────
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    """Clear the refresh token cookie — client should discard the access token."""
    response.delete_cookie("refresh_token")
