from fastapi import APIRouter, Depends
from supabase import Client

from ..database import get_db
from ..deps import get_current_user
from .schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


def _build_profile_response(user: dict, profile: dict) -> ProfileResponse:
    return ProfileResponse(
        user_id=str(user["id"]),
        email=user["email"],
        email_confirmed=user["email_confirmed"],
        full_name=profile.get("full_name"),
        zip_code=profile.get("zip_code"),
        phone=profile.get("phone"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
    )


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db),
):
    result = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    profile = result.data[0] if result.data else {}
    return _build_profile_response(current_user, profile)


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db),
):
    update_data = body.model_dump(exclude_none=True)
    if update_data:
        db.table("profiles").update(update_data).eq("user_id", current_user["id"]).execute()

    result = db.table("profiles").select("*").eq("user_id", current_user["id"]).execute()
    profile = result.data[0] if result.data else {}
    return _build_profile_response(current_user, profile)
