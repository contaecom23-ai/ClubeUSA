from supabase import create_client, Client
from .config import settings

# Única instância — service_role, nunca anon key.
# Toda query aqui é server-side; RLS não é a única barreira (checamos user_id no código).
_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client
