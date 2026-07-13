import secrets
import sys
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = ""

    # JWT
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email
    EMAIL_BACKEND: str = "console"  # console | resend
    EMAIL_FROM: str = "noreply@clubeusa.com"
    RESEND_API_KEY: str = ""

    # URLs
    APP_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:8000"

    # App
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "3/minute"

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()

# Fail hard if critical secrets are missing (never use defaults in production)
_missing = [k for k in ("DATABASE_URL", "SECRET_KEY") if not getattr(settings, k)]
if _missing and not settings.DEBUG:
    print(f"ERRO FATAL: variáveis de ambiente obrigatórias não configuradas: {_missing}", file=sys.stderr)
    sys.exit(1)

if not settings.SECRET_KEY and settings.DEBUG:
    # Dev-only fallback: warn loudly and use a random ephemeral key
    _ephemeral = secrets.token_hex(32)
    settings.SECRET_KEY = _ephemeral
    print(
        f"[AVISO] SECRET_KEY não configurada. Usando chave efêmera (sessions não sobrevivem ao restart). "
        f"Configure SECRET_KEY em .env para persistência.",
        file=sys.stderr,
    )
