import warnings
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Obrigatórios — startup falha se ausentes (sem defaults forjáveis)
    SECRET_KEY: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # Email SMTP
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@clubeusa.com"

    # App
    APP_NAME: str = "Clube USA"
    APP_URL: str = "http://localhost:8000"
    DEBUG: bool = False

    # Tokens
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_CONFIRM_TOKEN_EXPIRE_HOURS: int = 24

    # CORS (vírgula-separado)
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env"}


settings = Settings()  # type: ignore[call-arg]

if len(settings.SECRET_KEY) < 32:
    warnings.warn(
        "SECRET_KEY muito curta. Gere uma segura: "
        "python -c \"import secrets; print(secrets.token_urlsafe(32))\""
    )
