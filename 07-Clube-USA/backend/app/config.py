import secrets
import warnings
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # JWT
    secret_key: str = ""
    access_token_ttl_days: int = 7

    # URLs
    app_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # Email
    email_provider: str = "console"
    email_from: str = "noreply@clubeusa.com"
    email_api_key: str = ""

    @field_validator("secret_key", mode="before")
    @classmethod
    def require_secret_key(cls, v: str) -> str:
        if not v:
            generated = secrets.token_urlsafe(32)
            warnings.warn(
                "SECRET_KEY não definida — usando chave efêmera gerada automaticamente. "
                "Defina SECRET_KEY no .env para produção.",
                RuntimeWarning,
                stacklevel=2,
            )
            return generated
        return v

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
