from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.dependencies import get_current_user_id
from app.database import get_db
from app.users.schemas import ProfileResponse, UpdateProfileRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db),
):
    result = db.table("users") \
        .select("id, email, name, zip_code, state_abbr, email_verified, created_at") \
        .eq("id", user_id) \
        .execute()

    # user_id comes from validated JWT — should always exist; 404 on edge case
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return result.data[0]


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No fields to update.")

    if "state_abbr" in updates and updates["state_abbr"]:
        updates["state_abbr"] = updates["state_abbr"].upper()

    result = db.table("users") \
        .update(updates) \
        .eq("id", user_id) \
        .select("id, email, name, zip_code, state_abbr, email_verified, created_at") \
        .execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    return result.data[0]
