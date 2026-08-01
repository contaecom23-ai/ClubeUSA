import warnings
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Clube USA"
    debug: bool = False

    # Database
    database_url: str  # obrigatório — falha na inicialização se ausente

    # JWT — SECRET_KEY obrigatório, sem default forjável
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@clubeusa.com"

    # URLs
    frontend_url: str = "http://localhost:8000"
    allowed_origins: list[str] = ["http://localhost:8000", "http://localhost:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if len(s.secret_key) < 32:
        warnings.warn(
            "SECRET_KEY muito curta. Gere com: "
            "python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    return s
