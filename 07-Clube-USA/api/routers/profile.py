"""
Profile routes — all require authenticated user.
user_id always comes from the JWT (get_current_user_id dependency), never from request body.
IDOR is structurally impossible: every query is filtered by the token's user_id.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from ..database import get_db
from ..models.user import UpdateProfileRequest, UserPublic
from ..services.token_service import get_current_user_id

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserPublic)
async def get_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db),
) -> UserPublic:
    result = (
        db.table("users")
        .select("id, email, full_name, email_confirmed, created_at")
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        # Token valid but user deleted — treat as unauthorized
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")

    return UserPublic(**result.data[0])


@router.patch("/me", response_model=UserPublic)
async def update_my_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db),
) -> UserPublic:
    updates: dict = {"updated_at": datetime.now(timezone.utc).isoformat()}

    if body.full_name is not None:
        updates["full_name"] = body.full_name

    if len(updates) == 1:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    result = (
        db.table("users")
        .update(updates)
        .eq("id", user_id)
        .select("id, email, full_name, email_confirmed, created_at")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado.")

    return UserPublic(**result.data[0])
