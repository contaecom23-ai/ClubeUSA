from supabase import Client, create_client

from core.config import get_settings

_client: Client | None = None


def get_supabase() -> Client:
    """
    Retorna cliente Supabase inicializado com service_role key.
    Acesso exclusivo server-side; nunca expor ao browser.
    Singleton por processo.
    """
    global _client
    if _client is None:
        s = get_settings()
        _client = create_client(s.SUPABASE_URL, s.SUPABASE_SERVICE_ROLE_KEY)
    return _client
