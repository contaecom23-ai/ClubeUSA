import sys
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SITE_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:8000"
    APP_ENV: str = "development"

    @field_validator(
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_JWT_SECRET",
    )
    @classmethod
    def must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            print(
                "ERRO: variável de ambiente obrigatória está vazia. Verifique .env.",
                file=sys.stderr,
            )
            raise ValueError("Required environment variable is missing or empty")
        return v

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    model_config = {"env_file": ".env"}


settings = Settings()
