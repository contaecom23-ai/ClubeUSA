import os

from supabase import Client, create_client

_client: Client | None = None


def get_supabase() -> Client:
    """
    Retorna um cliente Supabase com service_role key (server-side only).
    A service_role key bypassa RLS — NUNCA exponha no frontend.
    """
    global _client
    if _client is None:
        url = os.environ.get("SUPABASE_URL", "")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY são obrigatórios"
            )
        _client = create_client(url, key)
    return _client
