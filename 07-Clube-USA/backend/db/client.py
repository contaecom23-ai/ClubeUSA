import os

_client = None


def get_supabase_client():
    """Singleton do cliente Supabase com service_role key (server-side apenas).

    Import lazy: o pacote supabase só é importado na primeira chamada real,
    permitindo que testes mockem esta função sem precisar instalar o supabase.
    Nunca expor service_role key no frontend. Toda query filtra por user_id
    vindo do JWT — nunca do input do cliente.
    """
    global _client
    if _client is None:
        from supabase import create_client  # noqa: PLC0415
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
        _client = create_client(url, key)
    return _client
