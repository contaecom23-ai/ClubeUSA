import sys
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    CORS_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:3000"]
    ENVIRONMENT: str = "development"


def _load() -> Settings:
    try:
        return Settings()
    except Exception as e:
        print(f"[FATAL] Variáveis de ambiente obrigatórias não configuradas: {e}", file=sys.stderr)
        sys.exit(1)


settings = _load()
