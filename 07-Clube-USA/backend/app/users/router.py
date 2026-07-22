from fastapi import APIRouter, Depends

from app.database import get_db
from app.dependencies import get_current_user_id
from app.users.schemas import MeResponse, ProfileResponse, ProfileUpdate
from app.users.service import get_me, update_profile

router = APIRouter(prefix="/api", tags=["users"])


@router.get("/me", response_model=MeResponse)
async def me(
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    return await get_me(db, user_id)


@router.put("/me/profile", response_model=ProfileResponse)
async def update_my_profile(
    body: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
    db=Depends(get_db),
):
    return await update_profile(db, user_id, body.model_dump())
