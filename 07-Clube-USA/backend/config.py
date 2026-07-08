import sys
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    app_name: str = "Clube USA"
    environment: str = "development"
    allowed_origins: list[str] = ["http://localhost:8000"]

    model_config = {"env_file": ".env", "case_sensitive": False}


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        try:
            _settings = Settings()
        except Exception as exc:
            print(
                f"ERRO CRÍTICO: variáveis de ambiente obrigatórias ausentes — {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    return _settings
