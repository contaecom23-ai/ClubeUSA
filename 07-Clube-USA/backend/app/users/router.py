from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.database import get_db
from app.dependencies import get_current_user_id
from app.users.models import UpdateProfileRequest, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
def get_me(user_id: str = Depends(get_current_user_id), db: Client = Depends(get_db)):
    result = (
        db.table("users")
        .select("id, email, full_name, city, state_abbr, email_confirmed, created_at")
        .eq("id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return result.data[0]


@router.put("/me", response_model=UserProfile)
def update_me(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: Client = Depends(get_db),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum campo para atualizar.")

    # Garante que só atualiza o próprio registro (dono vem do token, nunca do request)
    result = (
        db.table("users")
        .update(updates)
        .eq("id", user_id)
        .select("id, email, full_name, city, state_abbr, email_confirmed, created_at")
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return result.data[0]
