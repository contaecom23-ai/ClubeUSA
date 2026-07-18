import secrets
import sys
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # Generated randomly + warning if not set — required for production
    SECRET_KEY: str = ""

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60      # 1 hour
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Email: "log" (dev/test) | "resend" | "sendgrid"
    EMAIL_SERVICE: str = "log"
    RESEND_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    FROM_EMAIL: str = "noreply@clubeusa.com"

    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5500"
    CORS_ORIGINS: List[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]

    model_config = {"env_file": ".env"}

    def model_post_init(self, __context) -> None:
        if not self.SECRET_KEY:
            generated = secrets.token_urlsafe(32)
            object.__setattr__(self, "SECRET_KEY", generated)
            print(
                "WARNING: SECRET_KEY not set — using ephemeral random key. "
                "Set SECRET_KEY in .env before production.",
                file=sys.stderr,
            )


settings = Settings()
