from fastapi import APIRouter, Depends, HTTPException

from app.users.schemas import UpdateProfileRequest, UserProfile
from app.users.service import get_user_by_id, update_user_profile
from app.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(current_user: dict = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserProfile)
def update_me(body: UpdateProfileRequest, current_user: dict = Depends(get_current_user)):
    fields = body.non_empty_fields()
    updated = update_user_profile(current_user["id"], fields)
    if not updated:
        raise HTTPException(status_code=404, detail="Usuario nao encontrado")
    return updated
