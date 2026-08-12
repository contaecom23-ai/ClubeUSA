from functools import lru_cache
from typing import Optional

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def _get_client() -> Client:
    s = get_settings()
    return create_client(s.supabase_url, s.supabase_service_key)


def get_profile(user_id: str) -> Optional[dict]:
    """Busca o perfil do usuário. user_id sempre vem do JWT validado."""
    result = _get_client().table("profiles").select("*").eq("id", user_id).execute()
    return result.data[0] if result.data else None


def upsert_profile(user_id: str, fields: dict) -> dict:
    """Cria ou atualiza perfil. user_id sempre vem do JWT; nunca do cliente."""
    # Remove campos None para não sobrescrever dados existentes com null
    clean = {k: v for k, v in fields.items() if v is not None}
    if not clean:
        # Nada a atualizar — apenas retorna o perfil existente
        existing = get_profile(user_id)
        if existing:
            return existing
        clean = {}

    result = (
        _get_client()
        .table("profiles")
        .upsert({"id": user_id, **clean}, on_conflict="id")
        .execute()
    )
    return result.data[0]
