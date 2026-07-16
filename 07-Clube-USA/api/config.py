import os
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core secrets — app recusa iniciar em produção sem estes
    SECRET_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Auth TTLs
    ACCESS_TOKEN_TTL_DAYS: int = 7
    REFRESH_TOKEN_TTL_DAYS: int = 30
    EMAIL_CONFIRM_TOKEN_TTL_HOURS: int = 24

    # Email
    EMAIL_PROVIDER: str = "log"  # log | resend | sendgrid
    EMAIL_API_KEY: str = ""
    EMAIL_FROM: str = "noreply@clubeusa.com"

    # URLs
    FRONTEND_URL: str = "http://localhost:8000"
    API_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://localhost:3000"

    # Rate limits (formato slowapi: "N/period")
    LOGIN_RATE_LIMIT: str = "5/minute"
    REGISTER_RATE_LIMIT: str = "3/minute"

    ENVIRONMENT: str = "development"


def _load() -> Settings:
    s = Settings()
    is_testing = os.getenv("TESTING", "").lower() in ("1", "true", "yes")

    if not is_testing and s.ENVIRONMENT == "production":
        errors = []
        if len(s.SECRET_KEY) < 32:
            errors.append("SECRET_KEY ausente ou muito curta (mín. 32 chars). Gere com: python -c \"import secrets; print(secrets.token_urlsafe(32))\"")
        if not s.SUPABASE_URL:
            errors.append("SUPABASE_URL é obrigatória")
        if not s.SUPABASE_SERVICE_ROLE_KEY:
            errors.append("SUPABASE_SERVICE_ROLE_KEY é obrigatória")
        if errors:
            for e in errors:
                print(f"CONFIG ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    return s


settings = _load()
