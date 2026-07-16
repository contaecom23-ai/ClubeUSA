from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from deps import get_current_user_id, get_db
from models import UpdateProfileRequest, UserProfile
from supabase import Client

router = APIRouter(prefix="/users", tags=["users"])


def _row_to_profile(u: dict) -> UserProfile:
    return UserProfile(
        id=u["id"],
        email=u["email"],
        name=u["name"],
        phone=u.get("phone"),
        state=u.get("state"),
        city=u.get("city"),
        zip_code=u.get("zip_code"),
        email_confirmed=bool(u.get("email_confirmed_at")),
        referral_code=u.get("referral_code"),
        created_at=u["created_at"],
    )


def _fetch_user(db: Client, user_id: str) -> dict:
    result = (
        db.table("users")
        .select(
            "id, email, name, phone, state, city, zip_code, "
            "email_confirmed_at, referral_code, created_at"
        )
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return result.data[0]


@router.get("/me", response_model=UserProfile, summary="Obter perfil do usuário logado")
async def get_me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Client, Depends(get_db)],
) -> UserProfile:
    return _row_to_profile(_fetch_user(db, user_id))


@router.put("/me", response_model=UserProfile, summary="Atualizar perfil")
async def update_me(
    user_id: Annotated[str, Depends(get_current_user_id)],
    db: Annotated[Client, Depends(get_db)],
    body: UpdateProfileRequest,
) -> UserProfile:
    updates = body.model_dump(exclude_none=True)
    if updates:
        db.table("users").update(updates).eq("id", user_id).execute()
    return _row_to_profile(_fetch_user(db, user_id))
