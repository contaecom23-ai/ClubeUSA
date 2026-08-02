from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    ALLOWED_ORIGINS: str = "http://localhost:3000"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_LOGIN: str = "10/minute"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.ALLOWED_ORIGINS.split(",") if o.strip()]

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
