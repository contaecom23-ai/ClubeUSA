"""
Singleton do cliente Supabase (service_role).
Nunca expor ao browser — a chave service_role bypassa RLS.
"""
from __future__ import annotations

from typing import Optional

from supabase import AsyncClient, acreate_client

from app.config import settings

_client: Optional[AsyncClient] = None


async def init_db() -> None:
    global _client
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
        _client = await acreate_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )


async def get_db() -> AsyncClient:
    if _client is None:
        raise RuntimeError(
            "Supabase client não inicializado. "
            "Verifique SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY."
        )
    return _client
