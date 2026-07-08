from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..dependencies import get_current_user
from ..models.profile import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(user: dict = Depends(get_current_user)) -> ProfileResponse:
    db = get_db()
    result = (
        db.table("profiles")
        .select("*")
        .eq("id", user["id"])  # owner sempre do token
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )
    return ProfileResponse(**result.data, email=user["email"])


@router.put("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdate,
    user: dict = Depends(get_current_user),
) -> ProfileResponse:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar",
        )

    db = get_db()
    result = (
        db.table("profiles")
        .update(updates)
        .eq("id", user["id"])  # owner sempre do token
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado",
        )
    return ProfileResponse(**result.data[0], email=user["email"])
