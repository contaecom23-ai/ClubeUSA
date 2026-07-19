"""
Clientes Supabase:
- auth_client  → operações de autenticação (usa anon key)
- admin_client → operações de banco server-side (usa service_role key)

NUNCA exponha o admin_client ou service_role_key ao frontend.
"""
from functools import lru_cache
from supabase import create_client, Client
from app.config import settings


@lru_cache
def get_auth_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache
def get_admin_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
