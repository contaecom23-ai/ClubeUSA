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
    # Vazio = endpoints /admin desabilitados. Sem default forjável.
    # Gerar com: python -c "import secrets; print(secrets.token_urlsafe(32))"
    ADMIN_API_KEY: str = ""


def _load() -> Settings:
    try:
        s = Settings()
    except Exception as e:
        print(f"[FATAL] Variáveis de ambiente obrigatórias não configuradas: {e}", file=sys.stderr)
        sys.exit(1)
    if not s.ADMIN_API_KEY:
        print("[WARN] ADMIN_API_KEY não definida — /admin/analytics desabilitado.", file=sys.stderr)
    return s


settings = _load()
