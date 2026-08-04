from fastapi import APIRouter, Depends, HTTPException

from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import UpdateProfileRequest, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


def _to_user_response(u: dict) -> UserResponse:
    return UserResponse(
        id=u["id"],
        email=u["email"],
        full_name=u["full_name"],
        zip_code=u.get("zip_code"),
        referral_code=u["referral_code"],
        email_confirmed=bool(u.get("email_confirmed_at")),
        created_at=u["created_at"],
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return _to_user_response(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(body: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in {"full_name": body.full_name, "zip_code": body.zip_code}.items() if v is not None}
    if not updates:
        return _to_user_response(user)

    result = get_db().table("users").update(updates).eq("id", user["id"]).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao atualizar perfil")
    return _to_user_response(result.data[0])
