from supabase import create_client, Client
from .config import get_settings

_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        s = get_settings()
        _client = create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_KEY)
    return _client
