"""
Application settings — all values from environment variables.
No secret has a forgeable default; missing required vars raise at startup.
"""
import secrets
import sys
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")

    # ── App ───────────────────────────────────────────────────────────────────
    APP_NAME: str = "Clube USA API"
    DEBUG: bool = False
    FRONTEND_URL: str  # required; used in email confirmation links

    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY: str  # required; must be ≥ 32 random bytes (hex/urlsafe)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 1   # short-lived access token
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7  # refresh token — user must re-login after 7d

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str  # required
    SUPABASE_SERVICE_KEY: str  # required; SERVICE ROLE only — never anon key

    # ── CORS ──────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: str = ""  # comma-separated list of allowed origins

    # ── Email (SMTP) ──────────────────────────────────────────────────────────
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_TLS: bool = True

    # ── Rate limits ───────────────────────────────────────────────────────────
    RATE_LIMIT_LOGIN: str = "5/15minute"
    RATE_LIMIT_REGISTER: str = "10/hour"
    RATE_LIMIT_RESEND: str = "3/hour"

    @field_validator("SECRET_KEY")
    @classmethod
    def secret_key_strength(cls, v: str) -> str:
        if len(v) < 32:
            suggested = secrets.token_urlsafe(32)
            print(
                f"[FATAL] SECRET_KEY must be ≥ 32 chars.\n"
                f"  Generate one: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                f"  Suggested:    {suggested}",
                file=sys.stderr,
            )
            raise ValueError("SECRET_KEY too short (minimum 32 chars)")
        return v

    def get_allowed_origins(self) -> List[str]:
        if not self.ALLOWED_ORIGINS:
            return []
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
