from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user_id
from . import service
from .schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    user = await service.get_user(db, user_id)
    return ProfileResponse.model_validate(user)


@router.patch("/me", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    user = await service.update_profile(
        db,
        user_id,
        full_name=body.full_name,
        zip_code=body.zip_code,
        us_state=body.us_state,
        bio=body.bio,
    )
    return ProfileResponse.model_validate(user)
