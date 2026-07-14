from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.users import schemas, service

router = APIRouter()


@router.get("/me", response_model=schemas.ProfileResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return service.get_my_profile(
        user_id=current_user["user_id"],
        email=current_user["email"],
    )


@router.patch("/me", response_model=schemas.ProfileResponse)
def update_me(
    body: schemas.ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    return service.update_my_profile(
        user_id=current_user["user_id"],
        email=current_user["email"],
        updates=body,
    )
