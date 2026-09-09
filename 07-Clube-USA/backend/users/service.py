import logging
from supabase import Client
from fastapi import HTTPException, status
from users.schemas import ProfileResponse, ProfileUpdateRequest

logger = logging.getLogger(__name__)


def get_profile(supabase: Client, user_id: str) -> ProfileResponse:
    result = (
        supabase.table("profiles")
        .select("*")
        .eq("id", user_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")

    return ProfileResponse(**result.data)


def update_profile(
    supabase: Client, user_id: str, data: ProfileUpdateRequest
) -> ProfileResponse:
    updates = {k: v for k, v in data.model_dump().items() if v is not None}

    if not updates:
        return get_profile(supabase, user_id)

    result = (
        supabase.table("profiles")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")

    return ProfileResponse(**result.data[0])
