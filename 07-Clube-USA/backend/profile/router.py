import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from core.deps import get_confirmed_user
from core.supabase_client import get_supabase

from .schemas import ProfileResponse, ProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profile", tags=["profile"])

_PROFILE_FIELDS = "id, full_name, state, city, zip_code"


def _build_profile_response(user_id: str, email: str, data: dict) -> ProfileResponse:
    return ProfileResponse(
        id=user_id,
        email=email,
        full_name=data.get("full_name"),
        state=data.get("state"),
        city=data.get("city"),
        zip_code=data.get("zip_code"),
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    current_user: Annotated[dict, Depends(get_confirmed_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    user_id = current_user["id"]
    res = (
        supabase.table("profiles")
        .select(_PROFILE_FIELDS)
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )

    if not res.data:
        # Recover: create profile if it didn't get created during registration
        supabase.table("profiles").insert({"id": user_id}).execute()
        return ProfileResponse(id=user_id, email=current_user["email"])

    return _build_profile_response(user_id, current_user["email"], res.data)


@router.put("", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: Annotated[dict, Depends(get_confirmed_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    user_id = current_user["id"]
    update_data = body.model_dump(exclude_none=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    # user_id always comes from the token — never from client input (IDOR prevention)
    res = (
        supabase.table("profiles")
        .update(update_data)
        .eq("id", user_id)
        .execute()
    )

    if not res.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    return _build_profile_response(user_id, current_user["email"], res.data[0])
