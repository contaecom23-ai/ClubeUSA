from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    allowed_origins: str = "http://localhost:8000"


settings = Settings()
