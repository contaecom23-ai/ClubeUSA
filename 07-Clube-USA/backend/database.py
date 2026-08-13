from functools import lru_cache
from supabase import create_client, Client
from config import settings


@lru_cache(maxsize=1)
def get_user_client() -> Client:
    """Client com anon key — para operações de auth do usuário (sign_up, sign_in)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


@lru_cache(maxsize=1)
def get_admin_client() -> Client:
    """Client com service_role key — para operações de dados server-side (bypassa RLS)."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
