# app/core/security.py
# ─────────────────────────────────────────────────────────────────────────────
# Authentication utilities:
#   • Password hashing via pwdlib (Argon2 backend)
#   • JWT creation and verification via PyJWT
#
# WHY Argon2?  It is the winner of the Password Hashing Competition (2015) and
# is memory-hard, making GPU/ASIC brute-force attacks extremely expensive.
# ─────────────────────────────────────────────────────────────────────────────

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings

# ── Password hasher ───────────────────────────────────────────────────────────
# PasswordHash is the top-level pwdlib class; we give it Argon2Hasher as the
# only backend so no legacy bcrypt or pbkdf2 variants are accepted.
_pwd_hasher = PasswordHash([Argon2Hasher()])


def hash_password(plain_password: str) -> str:
    """
    Return the Argon2 hash of plain_password.
    The hash embeds the salt, the algorithm id, and the parameters so the
    stored string is fully self-describing.
    """
    return _pwd_hasher.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Constant-time comparison of plain_password against the stored hash.
    Returns True only when they match — never raises on mismatch.
    """
    return _pwd_hasher.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """
    Returns True if the hash was created with outdated parameters.
    Call this after a successful login to silently upgrade stored hashes.
    """
    return _pwd_hasher.check_needs_rehash(hashed_password)


# ── JWT helpers ───────────────────────────────────────────────────────────────

def _create_token(subject: str | Any, expires_delta: timedelta, extra: dict | None = None) -> str:
    """
    Internal helper — build and sign a JWT.

    Args:
        subject:      The 'sub' claim — typically the user's UUID string.
        expires_delta: How long until the token expires.
        extra:        Additional claims to merge into the payload (e.g. {'type': 'refresh'}).
    """
    now = datetime.now(UTC)                  # Always UTC — avoid tz-naive datetimes in JWTs
    payload: dict[str, Any] = {
        "sub": str(subject),                 # JWT subject — identifies the principal
        "iat": now,                          # Issued-At — lets us detect clock drift
        "exp": now + expires_delta,          # Expiry — PyJWT validates this automatically
    }
    if extra:
        payload.update(extra)

    # jwt.encode returns a str in PyJWT ≥ 2.x (no need to .decode())
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str | Any) -> str:
    """Short-lived token sent with every API request (Authorization: Bearer <token>)."""
    return _create_token(
        subject,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        extra={"type": "access"},
    )


def create_refresh_token(subject: str | Any) -> str:
    """
    Longer-lived token stored in an HttpOnly cookie.
    Used only to obtain a new access token — never for resource access.
    """
    return _create_token(
        subject,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        extra={"type": "refresh"},
    )


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate an access token.

    Raises:
        jwt.ExpiredSignatureError: Token has passed its expiry time.
        jwt.InvalidTokenError:     Signature invalid, malformed, or wrong type claim.
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],     # Restrict to configured algorithm — prevents alg:none attack
    )

    # Guard against using a refresh token where an access token is expected
    if payload.get("type") != "access":
        raise InvalidTokenError("Token type mismatch — expected 'access'")

    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a refresh token.

    Raises:
        jwt.ExpiredSignatureError: Token expired — user must re-authenticate.
        jwt.InvalidTokenError:     Bad signature or wrong type.
    """
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

    if payload.get("type") != "refresh":
        raise InvalidTokenError("Token type mismatch — expected 'refresh'")

    return payload
