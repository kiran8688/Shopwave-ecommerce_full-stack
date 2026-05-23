# app/core/config.py
# ─────────────────────────────────────────────────────────────────────────────
# Centralised application settings loaded from environment variables / .env
# Pydantic-Settings reads the .env file automatically; every field maps 1-to-1
# to an env-var of the same name (case-insensitive).
# ─────────────────────────────────────────────────────────────────────────────

from pydantic import AnyHttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "ShopWave E-Commerce API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False                      # Never True in production
    API_V1_PREFIX: str = "/api/v1"           # Versioned URL prefix for all routes

    # ── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: str                          # Must be set in .env — used for JWT signing
    ALGORITHM: str = "HS256"                 # HMAC-SHA256; symmetric, fast for internal services
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30    # Short-lived access token (30 min)
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7       # Longer-lived refresh token for re-authentication
    
    # Defaults for first admin user creation (bootstrapping)
    FIRST_ADMIN_EMAIL: str = "admin@shopwave.com"
    FIRST_ADMIN_PASSWORD: str = "AdminPassword123!"
    FIRST_ADMIN_USERNAME: str = "admin"

    # ── Database ─────────────────────────────────────────────────────────────
    # Full async DSN e.g.: postgresql+asyncpg://user:pass@db:5432/ecommerce
    DATABASE_URL: str                        # Set in docker-compose via environment block

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None) -> str | None:
        if isinstance(v, str):
            if v.startswith("postgres://"):
                return v.replace("postgres://", "postgresql+asyncpg://", 1)
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v


    # ── CORS — allowed origins for the React frontend ────────────────────────
    BACKEND_CORS_ORIGINS: str | list[AnyHttpUrl] = []

    # ── Allowed hosts for TrustedHostMiddleware ──────────────────────────────
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1", "*.onrender.com"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list) -> list:
        import json
        if isinstance(v, str) and not v.startswith("["):
            origins = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = v
        elif isinstance(v, str) and v.startswith("["):
             origins = json.loads(v)
        else:
            origins = []

        result = []
        for origin in origins:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                origin = f"https://{origin}"
            result.append(origin)
        return result

    # ── Pydantic-Settings config ──────────────────────────────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",          # Load from .env file in the working directory
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_ignore_empty=True
    )


# Singleton — import this object everywhere instead of instantiating Settings()
settings = Settings()
