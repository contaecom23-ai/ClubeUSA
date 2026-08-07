from fastapi import APIRouter, Depends, HTTPException, status

from database import get_db
from dependencies import get_current_user_id
from models import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(user_id: str = Depends(get_current_user_id)) -> ProfileResponse:
    db = get_db()

    # user_id vem do token — sem IDOR possível
    user_rows = (
        db.table("users")
        .select("id, email, is_email_confirmed")
        .eq("id", user_id)
        .execute()
    )
    if not user_rows.data:
        # 404, não 403 — não vazar existência de recursos de outros
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    profile_rows = db.table("profiles").select("*").eq("user_id", user_id).execute()

    user = user_rows.data[0]
    profile = profile_rows.data[0] if profile_rows.data else {}

    return ProfileResponse(
        user_id=user["id"],
        email=user["email"],
        is_email_confirmed=user["is_email_confirmed"],
        full_name=profile.get("full_name"),
        city=profile.get("city"),
        state=profile.get("state"),
        zip_code=profile.get("zip_code"),
        phone=profile.get("phone"),
        bio=profile.get("bio"),
        avatar_url=profile.get("avatar_url"),
    )


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    body: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
) -> ProfileResponse:
    db = get_db()

    # Confirmar que o user existe (token pode ser de conta deletada)
    user_rows = (
        db.table("users")
        .select("id, email, is_email_confirmed")
        .eq("id", user_id)
        .execute()
    )
    if not user_rows.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")

    # Atualizar apenas campos fornecidos (excluir None)
    updates = body.model_dump(exclude_none=True)
    if updates:
        profile_exists = db.table("profiles").select("id").eq("user_id", user_id).execute()
        if profile_exists.data:
            db.table("profiles").update(updates).eq("user_id", user_id).execute()
        else:
            db.table("profiles").insert({"user_id": user_id, **updates}).execute()

    return get_my_profile(user_id=user_id)
