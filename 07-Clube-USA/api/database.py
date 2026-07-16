from functools import lru_cache

from supabase import Client, create_client

from config import settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    """Retorna cliente Supabase com service_role (acesso server-side, nunca expor ao client)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórias. Veja .env.example"
        )
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
