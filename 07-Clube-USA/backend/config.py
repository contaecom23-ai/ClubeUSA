import warnings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Obrigatórios (sem default — startup falha se ausentes) ---
    DATABASE_URL: str  # Ex: postgresql://user:pass@host:5432/dbname
    SECRET_KEY: str    # Gerar: python -c "import secrets; print(secrets.token_urlsafe(32))"

    # --- Auth ---
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # --- Email ---
    EMAIL_FROM: str = "noreply@clubeusa.com"
    EMAIL_FROM_NAME: str = "Clube USA"
    SMTP_HOST: str = ""      # vazio = modo console (log no stdout)
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True

    # --- App ---
    APP_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:8000,http://localhost:3000"

    # --- Rate limiting ---
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    model_config = {"env_file": ".env", "extra": "ignore"}


def _load_settings() -> Settings:
    s = Settings()
    if not s.SECRET_KEY or len(s.SECRET_KEY) < 32:
        warnings.warn(
            "SECRET_KEY ausente ou fraco. Gere com: "
            "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    return s


settings = _load_settings()
