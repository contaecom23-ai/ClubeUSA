import secrets
import warnings
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase (server-side service_role only — never expose to client)
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_DAYS: int = 7

    # App
    FRONTEND_URL: str = "http://localhost:8080"
    BACKEND_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:8080,http://localhost:3000"

    # Email (SMTP); empty = dev mode (print link to console)
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@clubeusa.com"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def model_post_init(self, __context) -> None:
        insecure = {"", "REPLACE-WITH-A-RANDOM-64-CHAR-STRING", "change-me", "secret"}
        if self.SECRET_KEY in insecure or len(self.SECRET_KEY) < 32:
            suggestion = secrets.token_urlsafe(64)
            warnings.warn(
                "SECRET_KEY is missing or insecure. "
                f"Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
                f"Example: {suggestion}",
                UserWarning,
                stacklevel=2,
            )


settings = Settings()
