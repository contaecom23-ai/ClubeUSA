from supabase import Client, create_client

from core.config import settings

# Singleton client using service_role key — bypasses RLS, backend use only.
# NEVER pass this client or the service key to the frontend.
_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _client
