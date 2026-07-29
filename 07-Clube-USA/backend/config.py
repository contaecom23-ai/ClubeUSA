import secrets
import warnings
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_days: int = 7
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@clubeusa.com"
    app_url: str = "http://localhost:8000"
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"
    debug: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def model_post_init(self, __context: object) -> None:
        if not self.jwt_secret_key:
            warnings.warn(
                "JWT_SECRET_KEY not set — generated a random one. "
                "Set JWT_SECRET_KEY in .env or all existing tokens will be invalidated on restart.",
                RuntimeWarning,
                stacklevel=2,
            )
            object.__setattr__(self, "jwt_secret_key", secrets.token_hex(64))


settings = Settings()
