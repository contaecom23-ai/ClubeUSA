from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    app_name: str = "Clube USA API"
    environment: str = "development"
    frontend_url: str = "http://localhost:8080"

    # JWT — access token 7 days, refresh 30 days
    secret_key: str = ""
    access_token_expire_minutes: int = 60 * 24 * 7
    refresh_token_expire_days: int = 30

    # Supabase (always service_role — never anon key from the backend)
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    # SMTP (see DECISOES.md for provider choice)
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@clubeusa.com"

    # CORS
    allowed_origins: str = "http://localhost:8080,http://localhost:3000"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def get_allowed_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    s = Settings()
    if not s.secret_key or s.secret_key == "CHANGE_ME_generate_a_random_64_char_secret":
        raise ValueError(
            "SECRET_KEY must be set to a secure random value.\n"
            "Generate: python -c \"import secrets; print(secrets.token_urlsafe(64))\""
        )
    if not s.supabase_url:
        raise ValueError("SUPABASE_URL must be set")
    if not s.supabase_service_role_key:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY must be set")
    return s
