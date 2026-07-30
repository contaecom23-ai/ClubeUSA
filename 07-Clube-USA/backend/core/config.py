import secrets
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # JWT — must be set via env, never use a default in prod
    secret_key: str = ""

    # App
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    app_base_url: str = "http://localhost:8000"

    # Email
    email_from: str = "noreply@clubeusa.com"

    # Token TTLs (seconds)
    access_token_ttl: int = 30 * 60       # 30 minutes
    refresh_token_ttl: int = 7 * 24 * 3600  # 7 days
    email_confirm_ttl: int = 24 * 3600    # 24 hours

    def __init__(self, **data):
        super().__init__(**data)
        if not self.secret_key:
            if self.environment == "production":
                print("FATAL: SECRET_KEY env var is required in production", file=sys.stderr)
                sys.exit(1)
            # Development only: generate ephemeral key with a loud warning
            self.secret_key = secrets.token_hex(64)
            print("WARNING: SECRET_KEY not set — using ephemeral key. Sessions will reset on restart.", file=sys.stderr)

    @property
    def origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
