import secrets
import sys
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM: str = "noreply@clubeusa.com"
    EMAIL_FROM_NAME: str = "Clube USA"

    APP_URL: str = "http://localhost:8000"
    API_URL: str = "http://localhost:8000"
    ENV: str = "development"
    ALLOWED_ORIGINS: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.SECRET_KEY:
        if s.ENV == "production":
            print("CRITICAL: SECRET_KEY must be set in production. Exiting.", file=sys.stderr)
            sys.exit(1)
        s.SECRET_KEY = secrets.token_hex(32)
        print("WARNING: SECRET_KEY not set — using a random key. Tokens won't survive restarts.", file=sys.stderr)
    if not s.DATABASE_URL:
        print("CRITICAL: DATABASE_URL is not set. Exiting.", file=sys.stderr)
        sys.exit(1)
    return s
