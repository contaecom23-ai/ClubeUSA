import secrets
import warnings
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "Clube USA API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    APP_URL: str = "http://localhost:8000"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./clubeusa_dev.db"

    # JWT
    SECRET_KEY: str = ""
    ACCESS_TOKEN_TTL_SECONDS: int = 7 * 24 * 60 * 60   # 7 dias
    REFRESH_TOKEN_TTL_SECONDS: int = 30 * 24 * 60 * 60  # 30 dias
    ALGORITHM: str = "HS256"

    # Tokens de confirmação de e-mail / reset de senha
    EMAIL_CONFIRM_TOKEN_TTL_SECONDS: int = 24 * 60 * 60  # 24 horas
    PASSWORD_RESET_TOKEN_TTL_SECONDS: int = 2 * 60 * 60  # 2 horas

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # E-mail
    EMAIL_BACKEND: str = "console"  # "console" | "resend" | "sendgrid"
    EMAIL_FROM: str = "noreply@clubeusa.com"
    EMAIL_FROM_NAME: str = "Clube USA"
    RESEND_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "10/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"

    def model_post_init(self, __context: object) -> None:
        if not self.SECRET_KEY:
            generated = secrets.token_urlsafe(64)
            warnings.warn(
                "SECRET_KEY não definido! Usando chave efêmera — INSEGURO para produção. "
                "Defina SECRET_KEY no .env.",
                stacklevel=2,
            )
            # Pydantic v2: usar object.__setattr__ para burlar imutabilidade
            object.__setattr__(self, "SECRET_KEY", generated)

        if self.ENVIRONMENT == "production" and self.DATABASE_URL.startswith("sqlite"):
            raise ValueError("SQLite não permitido em ENVIRONMENT=production.")


settings = Settings()
