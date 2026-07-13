from functools import lru_cache
from supabase import create_client, Client
from app.config import get_settings


@lru_cache()
def get_db() -> Client:
    s = get_settings()
    # service_role key only — never expose to the client side
    return create_client(s.supabase_url, s.supabase_service_role_key)
