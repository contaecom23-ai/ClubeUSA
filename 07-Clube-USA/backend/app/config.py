import sys
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str

    CORS_ORIGINS: str = ""
    APP_ENV: str = "development"

    @property
    def cors_origins_list(self) -> list[str]:
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    def _validate_secrets(self) -> None:
        """Recusa iniciar se algum segredo parece placeholder."""
        sentinels = {"xxxx", "eyJ...", "super-secret", "changeme", "secret"}
        for field in ("SUPABASE_URL", "SUPABASE_ANON_KEY",
                      "SUPABASE_SERVICE_ROLE_KEY", "SUPABASE_JWT_SECRET"):
            val = getattr(self, field, "")
            if any(s in val for s in sentinels):
                print(
                    f"[ERRO] {field} parece placeholder. "
                    "Configure as variáveis de ambiente reais antes de iniciar.",
                    file=sys.stderr,
                )
                sys.exit(1)


@lru_cache
def get_settings() -> Settings:
    s = Settings()  # type: ignore[call-arg]
    if s.APP_ENV != "testing":
        s._validate_secrets()
    return s


settings = get_settings()
