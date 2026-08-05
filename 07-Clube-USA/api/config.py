import sys
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # ── Required ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str  # service_role — never exposed to clients
    SECRET_KEY: str            # JWT signing; min 32 chars

    # ── App ───────────────────────────────────────────────────────────────────
    APP_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    CONFIRMATION_TOKEN_EXPIRE_HOURS: int = 24
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    # ── SMTP (blank = log to console in dev) ─────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@clubeusa.com"
    SMTP_USE_TLS: bool = True

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_strength(cls, v: str) -> str:
        if not v or len(v) < 32:
            raise ValueError(
                "SECRET_KEY must be ≥32 chars. "
                "Generate: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return v


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as exc:
        print(f"[FATAL] Configuration error: {exc}", file=sys.stderr)
        raise
