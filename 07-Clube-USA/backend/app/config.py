import secrets
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Supabase — server-side only (service_role key)
    supabase_url: str = "https://placeholder.supabase.co"
    supabase_service_role_key: str = "placeholder"

    # JWT
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days

    # Email
    email_from: str = "noreply@clubeusa.com"
    email_from_name: str = "Clube USA"
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""

    # App
    app_url: str = "http://localhost:5500"
    environment: str = "development"

    # CORS — comma-separated
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"

    def model_post_init(self, __context) -> None:
        if not self.secret_key:
            if self.environment == "production":
                print("FATAL: SECRET_KEY must be set in production.", file=sys.stderr)
                sys.exit(1)
            object.__setattr__(self, "secret_key", secrets.token_urlsafe(48))
            print(
                "WARNING: SECRET_KEY not set — ephemeral key generated. "
                "Tokens will NOT survive restart. Set SECRET_KEY in .env.",
                file=sys.stderr,
            )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
