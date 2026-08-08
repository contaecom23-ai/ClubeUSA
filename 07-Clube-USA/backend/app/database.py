from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_db() -> Client:
    s = get_settings()
    # service_role: acesso total server-side; nunca expor ao client
    return create_client(s.supabase_url, s.supabase_service_role_key)
