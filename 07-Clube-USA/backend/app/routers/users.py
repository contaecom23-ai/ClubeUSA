from fastapi import APIRouter, Depends, HTTPException
from supabase import Client

from app.dependencies import get_current_user, get_supabase
from app.schemas.user import ProfileResponse, UpdateProfileRequest

router = APIRouter(prefix="/users", tags=["users"])


def _fetch_profile(supabase: Client, user_id: str) -> dict:
    result = (
        supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return result.data


@router.get("/me", response_model=ProfileResponse)
def get_me(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ProfileResponse:
    user_id = current_user["sub"]
    profile = _fetch_profile(supabase, user_id)
    return ProfileResponse(
        id=profile["id"],
        email=current_user.get("email", ""),
        first_name=profile["first_name"],
        last_name=profile["last_name"],
        zip_code=profile["zip_code"],
        phone=profile.get("phone"),
        created_at=profile["created_at"],
        updated_at=profile["updated_at"],
    )


@router.patch("/me", response_model=ProfileResponse)
def update_me(
    body: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> ProfileResponse:
    user_id = current_user["sub"]

    updates = body.model_dump(exclude_unset=True, exclude_none=False)
    if not updates:
        raise HTTPException(400, "Nenhum campo para atualizar")

    result = (
        supabase.table("profiles")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Perfil não encontrado")

    updated = result.data[0]
    return ProfileResponse(
        id=updated["id"],
        email=current_user.get("email", ""),
        first_name=updated["first_name"],
        last_name=updated["last_name"],
        zip_code=updated["zip_code"],
        phone=updated.get("phone"),
        created_at=updated["created_at"],
        updated_at=updated["updated_at"],
    )
