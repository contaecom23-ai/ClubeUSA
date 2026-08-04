import os
import sys
import secrets
import logging

logger = logging.getLogger(__name__)


def _require(key: str) -> str:
    val = os.getenv(key, "").strip()
    if not val:
        logger.critical("FATAL: env var %s ausente — encerrando", key)
        sys.exit(1)
    return val


def _secret(key: str) -> str:
    """Requer em produção; gera aleatório em dev com aviso."""
    val = os.getenv(key, "").strip()
    if not val:
        generated = secrets.token_hex(32)
        logger.warning(
            "AVISO: %s não definido — usando valor aleatório. "
            "INSEGURO para produção: tokens invalidados ao reiniciar.",
            key,
        )
        return generated
    return val


class Settings:
    SECRET_KEY: str = _secret("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    SUPABASE_URL: str = _require("SUPABASE_URL")
    SUPABASE_SERVICE_KEY: str = _require("SUPABASE_SERVICE_KEY")

    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@clubeusa.com")

    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8080")
    ALLOWED_ORIGINS: list = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS", "http://localhost:8080,http://localhost:3000"
        ).split(",")
        if o.strip()
    ]

    EMAIL_CONFIRMATION_EXPIRE_HOURS: int = 24

    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_RESEND: str = "3/minute"


settings = Settings()
