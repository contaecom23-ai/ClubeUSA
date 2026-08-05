import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Supabase (obrigatórios — sem default forjável)
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    # App
    APP_ENV: str = "development"
    FRONTEND_URL: str = "http://localhost:8000"
    ALLOWED_ORIGINS: str = "http://localhost:8000"

    # Rate limits
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    model_config = {"env_file": ".env"}

    def model_post_init(self, __context: object) -> None:
        if len(self.SUPABASE_JWT_SECRET) < 32:
            warnings.warn(
                "SUPABASE_JWT_SECRET parece muito curto. "
                "Use o secret real do painel Supabase (Settings > API).",
                stacklevel=2,
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
