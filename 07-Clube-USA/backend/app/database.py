"""
Singleton do cliente Supabase (service_role — nunca anon key com dados sensíveis).
Todas as queries passam pelo servidor; RLS do Supabase é o endgame mas por ora
o isolamento multi-tenant é feito no nível da aplicação (filtro por user_id
vindo sempre do token, nunca do input do cliente).
"""
from typing import Optional

from supabase import AsyncClient, acreate_client

from app.config import settings

_client: Optional[AsyncClient] = None


async def get_db() -> AsyncClient:
    global _client
    if _client is None:
        _client = await acreate_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
    return _client
