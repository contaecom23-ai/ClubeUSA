from supabase import Client, create_client

from app.config import settings

_client: Client | None = None


def get_db() -> Client:
    """Return a singleton Supabase client using the service_role key.

    server-side only — the service_role key is NEVER sent to the browser.
    """
    global _client
    if _client is None:
        _client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _client
