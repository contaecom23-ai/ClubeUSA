from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from core.deps import get_current_user_id
from db.client import get_db
from schemas.profile import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


def _get_profile_or_404(db: Client, user_id: str) -> dict:
    """Fetch profile + email data for the given user.

    Always filters by user_id from the JWT — IDOR-safe.
    Short-circuits after the first empty result to avoid unnecessary queries.
    """
    profile_result = db.table("profiles").select("*").eq("user_id", user_id).execute()
    if not profile_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")

    user_result = db.table("users").select("email, email_confirmed").eq("id", user_id).execute()
    if not user_result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado.")

    p = profile_result.data[0]
    u = user_result.data[0]
    return {**p, "email": u["email"], "email_confirmed": u["email_confirmed"]}


@router.get("/me", response_model=ProfileResponse)
async def get_my_profile(
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return _get_profile_or_404(db, user_id)


@router.patch("/me", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdateRequest,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return _get_profile_or_404(db, user_id)

    db.table("profiles").update(updates).eq("user_id", user_id).execute()
    return _get_profile_or_404(db, user_id)
