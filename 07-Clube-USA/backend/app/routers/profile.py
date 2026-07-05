import logging

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas import ProfileResponse, ProfileUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_profile_response(user: dict, profile: dict) -> ProfileResponse:
    return ProfileResponse(
        user_id=user["id"],
        email=user["email"],
        full_name=profile.get("full_name"),
        phone=profile.get("phone"),
        state=profile.get("state"),
        city=profile.get("city"),
        zip_code=profile.get("zip_code"),
        is_email_verified=user["is_email_verified"],
        created_at=profile.get("created_at", ""),
    )


def _get_or_create_profile(db: Client, user_id: str) -> dict:
    """Fetch profile, creating a blank one if registration left it missing."""
    result = db.table("profiles").select("*").eq("user_id", user_id).execute()
    if result.data:
        return result.data[0]

    db.table("profiles").insert({"user_id": user_id}).execute()
    result = db.table("profiles").select("*").eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao carregar perfil.",
        )
    return result.data[0]


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> ProfileResponse:
    """Return the authenticated user's profile.

    user_id comes from the validated JWT token — never from the request.
    """
    profile = _get_or_create_profile(db, current_user["id"])
    return _build_profile_response(current_user, profile)


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db),
) -> ProfileResponse:
    """Update the authenticated user's profile fields.

    Only provided (non-null) fields are updated.
    user_id is always taken from the server-side token, never from the body.
    """
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar.",
        )

    user_id = current_user["id"]

    # Ensure profile exists before updating
    _get_or_create_profile(db, user_id)

    db.table("profiles").update(updates).eq("user_id", user_id).execute()

    profile = _get_or_create_profile(db, user_id)
    return _build_profile_response(current_user, profile)
