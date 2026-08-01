from fastapi import APIRouter, Depends, Header

from ..auth.service import get_current_user_id
from ..database import get_db
from .schemas import UpdateProfileRequest, UserProfile
from .service import get_my_profile, update_my_profile

router = APIRouter(prefix="/users", tags=["users"])


async def _current_user(
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
) -> tuple[str, object]:
    user_id = await get_current_user_id(authorization, db)
    return user_id, db


@router.get("/me", response_model=UserProfile)
async def me(ctx=Depends(_current_user)):
    user_id, db = ctx
    return await get_my_profile(user_id, db)


@router.put("/me", response_model=UserProfile)
async def update_me(data: UpdateProfileRequest, ctx=Depends(_current_user)):
    user_id, db = ctx
    return await update_my_profile(user_id, data, db)
