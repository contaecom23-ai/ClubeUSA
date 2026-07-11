import secrets
import sys
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── Database (Supabase) ─────────────────────────────────────────────────
    supabase_url: str
    supabase_service_role_key: str  # server-side only, never exposed to client

    # ── JWT ──────────────────────────────────────────────────────────────────
    # Must be set via env var; random default only in test env to prevent startup failure.
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    jwt_refresh_token_expire_days: int = 30

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "Clube USA"
    app_base_url: str = "http://localhost:8000"
    environment: str = "development"

    # ── Email ────────────────────────────────────────────────────────────────
    # Set EMAIL_PROVIDER=smtp or EMAIL_PROVIDER=log (default for dev)
    email_provider: str = "log"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from_address: str = "noreply@clubeusa.com"
    email_from_name: str = "Clube USA"

    # ── CORS ─────────────────────────────────────────────────────────────────
    # Comma-separated list of allowed origins.
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # ── Rate limiting ────────────────────────────────────────────────────────
    rate_limit_login_max: int = 10         # attempts per window
    rate_limit_login_window_seconds: int = 900  # 15 min
    rate_limit_register_max: int = 5
    rate_limit_register_window_seconds: int = 3600  # 1 hour

    def validate_secrets(self) -> None:
        """Fail loudly at startup if critical secrets are missing or weak."""
        missing = []
        if not self.supabase_url:
            missing.append("SUPABASE_URL")
        if not self.supabase_service_role_key:
            missing.append("SUPABASE_SERVICE_ROLE_KEY")
        if not self.jwt_secret:
            missing.append("JWT_SECRET")
        elif len(self.jwt_secret) < 32:
            print("WARNING: JWT_SECRET is shorter than 32 chars — use secrets.token_urlsafe(64)", file=sys.stderr)

        if missing and self.environment != "test":
            raise RuntimeError(
                f"Missing required env vars: {', '.join(missing)}. "
                "Set them before starting the server."
            )

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.validate_secrets()
    return s
