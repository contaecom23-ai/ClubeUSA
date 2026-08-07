import sys
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Required — sem defaults; faltando = erro explícito na inicialização
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str  # service_role, NUNCA anon key
    JWT_SECRET: str  # gere com: secrets.token_hex(32)

    # Email
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@clubeusa.com"
    EMAIL_ENABLED: bool = False  # False em dev — loga o link no console

    # URLs
    FRONTEND_URL: str = "http://localhost:8080"
    ALLOWED_ORIGINS: str = "http://localhost:8080"

    # JWT / tokens
    JWT_ALGORITHM: str = "HS256"
    JWT_TTL_DAYS: int = 7
    EMAIL_TOKEN_TTL_HOURS: int = 24

    # Rate limits (formato slowapi)
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if len(s.JWT_SECRET) < 32:
        print(
            "[SECURITY WARNING] JWT_SECRET tem menos de 32 chars — use secrets.token_hex(32)",
            file=sys.stderr,
        )
    return s
