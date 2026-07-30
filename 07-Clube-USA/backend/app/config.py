import sys
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str
    SECRET_KEY: str

    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_CONFIRM_EXPIRE_HOURS: int = 24

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@clubeusa.com"
    SMTP_TLS: bool = True

    ALLOWED_ORIGINS: str = "http://localhost:3000"
    APP_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"
    TESTING: bool = False

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",")]

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)


def _load_settings() -> Settings:
    try:
        s = Settings()  # type: ignore[call-arg]
    except Exception as e:
        print(f"ERRO: configuração inválida — {e}", file=sys.stderr)
        print("Copie .env.example para .env e preencha os valores.", file=sys.stderr)
        sys.exit(1)
    if not s.SECRET_KEY:
        print("ERRO: SECRET_KEY é obrigatória.", file=sys.stderr)
        print("Gere com: python -c \"import secrets; print(secrets.token_urlsafe(32))\"", file=sys.stderr)
        sys.exit(1)
    return s


settings = _load_settings()
