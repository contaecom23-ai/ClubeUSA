from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models import User
from app.schemas import ProfileResponse, ProfileUpdateRequest
from app.users import service as users_service

router = APIRouter(prefix="/users", tags=["users"])


def _to_profile(user: User) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        state_us=user.state_us,
        city=user.city,
        zip_code=user.zip_code,
        is_email_confirmed=user.is_email_confirmed,
        created_at=user.created_at,
    )


@router.get("/me", response_model=ProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return _to_profile(current_user)


@router.patch("/me", response_model=ProfileResponse)
async def update_me(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    updated = await users_service.update_profile(db, current_user, data)
    return _to_profile(updated)
