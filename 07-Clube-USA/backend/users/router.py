from fastapi import APIRouter, Depends
from supabase import Client

from core.deps import get_current_user_id
from db.supabase import get_supabase
from users.schemas import ProfileResponse, ProfileUpdateRequest
from users.service import get_profile, update_profile

router = APIRouter(tags=["users"])


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase),
):
    return get_profile(supabase, user_id)


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    supabase: Client = Depends(get_supabase),
):
    return update_profile(supabase, user_id, data)
