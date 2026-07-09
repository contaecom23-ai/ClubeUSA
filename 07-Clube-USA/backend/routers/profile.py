from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from auth.middleware import get_current_user
from db.client import get_supabase_client

router = APIRouter()

UPDATABLE_FIELDS = {"full_name", "city", "state_us", "phone"}


class ProfileUpdate(BaseModel):
    full_name: Optional[Annotated[str, Field(min_length=1, max_length=100)]] = None
    city: Optional[Annotated[str, Field(max_length=100)]] = None
    state_us: Optional[Annotated[str, Field(min_length=2, max_length=2)]] = None
    phone: Optional[Annotated[str, Field(max_length=20)]] = None


def _fetch_profile(user_id: str) -> dict:
    """Busca perfil pelo user_id. Sempre filtra pelo dono — nunca pelo input do cliente."""
    result = (
        get_supabase_client()
        .table("profiles")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return result.data


@router.get("")
async def get_profile(user: dict = Depends(get_current_user)) -> dict:
    return _fetch_profile(user["user_id"])


@router.patch("")
async def update_profile(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
) -> dict:
    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # Garante que só campos permitidos chegam ao banco
    update_data = {k: v for k, v in update_data.items() if k in UPDATABLE_FIELDS}

    result = (
        get_supabase_client()
        .table("profiles")
        .update(update_data)
        .eq("id", user["user_id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return result.data[0]
