import os
import sys
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Falha explicitamente se variável de ambiente crítica estiver ausente."""
    val = os.getenv(key)
    if not val:
        print(
            f"ERRO FATAL: variável de ambiente '{key}' não definida. "
            "Copie .env.example para .env e preencha todos os campos obrigatórios.",
            file=sys.stderr,
        )
        sys.exit(1)
    return val


class Settings:
    # Banco de dados
    DATABASE_URL: str = _require("DATABASE_URL")

    # JWT — sem default forjável; falha se ausente
    SECRET_KEY: str = _require("SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    EMAIL_TOKEN_EXPIRE_HOURS: int = 24

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
        if o.strip()
    ]

    # Email (SMTP)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "noreply@clubeusa.com")
    SMTP_FROM_NAME: str = os.getenv("SMTP_FROM_NAME", "Clube USA")

    # URL base do frontend (usada nos links de email)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


settings = Settings()
