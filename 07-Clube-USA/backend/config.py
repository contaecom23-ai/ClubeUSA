import os
from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_service_role_key: str

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_days: int = 7

    # Email SMTP (opcional — sem config o link de confirmação é logado)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@clubeusa.com"

    # URLs
    app_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:3000"
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("secret_key")
    @classmethod
    def secret_key_strong(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError(
                "SECRET_KEY deve ter ao menos 32 caracteres. "
                'Gere com: python -c "import secrets; print(secrets.token_urlsafe(64))"'
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_nested_delimiter": None,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
