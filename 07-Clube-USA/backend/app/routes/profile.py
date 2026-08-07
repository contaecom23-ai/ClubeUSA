from fastapi import APIRouter, Depends

from app.database import Database
from app.dependencies import get_current_user, get_db
from app.models.user import UserProfile, UserProfileUpdate

router = APIRouter(prefix="/me", tags=["profile"])


@router.get("", response_model=UserProfile)
def get_profile(current_user: dict = Depends(get_current_user)):
    return UserProfile.from_db(current_user)


@router.patch("", response_model=UserProfile)
def update_profile(
    body: UserProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Database = Depends(get_db),
):
    # Only send fields that were explicitly provided (not None by omission)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return UserProfile.from_db(current_user)

    # user_id always comes from the validated token — never from the request body
    updated = db.update_user_profile(user_id=current_user["id"], data=updates)
    return UserProfile.from_db(updated)
