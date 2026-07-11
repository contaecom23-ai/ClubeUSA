"""
Supabase client — service role only.
RLS is the end goal; until then all queries go server-side via service_role key.
The anon key is never used here.
"""
from functools import lru_cache

from supabase import Client, create_client

from .config import settings


@lru_cache
def get_db() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
