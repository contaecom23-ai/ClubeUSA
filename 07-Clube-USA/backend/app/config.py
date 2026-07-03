import secrets
import warnings
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = ""
    SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@clubeusa.com"
    SMTP_TLS: bool = True

    APP_BASE_URL: str = "http://localhost:8000"
    CORS_ORIGINS: list[str] = ["http://localhost:8000", "http://localhost:3000"]
    ENVIRONMENT: str = "development"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    def model_post_init(self, __context: object) -> None:
        if not self.SECRET_KEY:
            generated = secrets.token_hex(32)
            warnings.warn(
                "SECRET_KEY não definida! Usando chave efêmera — todas as sessões "
                "serão invalidadas ao reiniciar. Defina SECRET_KEY no .env para produção.",
                UserWarning,
                stacklevel=2,
            )
            object.__setattr__(self, "SECRET_KEY", generated)

        if not self.DATABASE_URL and self.ENVIRONMENT != "test":
            warnings.warn(
                "DATABASE_URL não definida! A aplicação não conseguirá conectar ao banco.",
                UserWarning,
                stacklevel=2,
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
