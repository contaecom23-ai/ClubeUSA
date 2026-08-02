import secrets
import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # JWT
    secret_key: str
    access_token_ttl_days: int = 7

    # Email
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_pass: str = ""
    email_from: str = "noreply@clubeusa.com"
    email_from_name: str = "Clube USA"

    # App
    app_base_url: str = "http://localhost:8000"
    environment: str = "development"
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.environment == "development"


def _load_settings() -> Settings:
    try:
        s = Settings()  # type: ignore[call-arg]
    except Exception as exc:
        print(f"[CONFIG ERROR] {exc}", file=sys.stderr)
        print(
            "Copie .env.example para .env e preencha as variáveis obrigatórias.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not s.secret_key or len(s.secret_key) < 32:
        print(
            "[SECURITY] SECRET_KEY ausente ou fraca. "
            f"Gere com: python -c \"import secrets; print(secrets.token_urlsafe(64))\"",
            file=sys.stderr,
        )
        sys.exit(1)

    return s


settings = _load_settings()
