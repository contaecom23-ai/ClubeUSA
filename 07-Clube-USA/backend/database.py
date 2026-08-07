from functools import lru_cache
from supabase import create_client, Client
from config import get_settings


@lru_cache
def get_db() -> Client:
    s = get_settings()
    # service_role bypassa RLS — toda query DEVE filtrar por user_id no backend
    return create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_KEY)
