from supabase import create_client, Client
from .config import settings

_client: Client | None = None


def get_db() -> Client:
    """Singleton — service_role bypassa RLS; acesso exclusivo do backend."""
    global _client
    if _client is None:
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
    return _client
