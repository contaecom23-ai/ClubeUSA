from fastapi import APIRouter, Depends, HTTPException, status

from ..database import get_db
from ..deps import get_current_user_id
from ..models import MessageResponse, ProfileUpdate, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


def _fetch_user_with_profile(user_id: str) -> dict:
    db = get_db()
    user_res = db.table("users").select(
        "id,email,full_name,email_confirmed,created_at"
    ).eq("id", user_id).execute()

    if not user_res.data:
        # Não deve acontecer se o token é válido, mas protege contra race condition
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    profile_res = db.table("profiles").select(
        "city,state,zip_code,bio"
    ).eq("user_id", user_id).execute()

    profile = profile_res.data[0] if profile_res.data else {}
    return {**user_res.data[0], **profile}


@router.get("/me", response_model=UserProfile)
async def get_me(user_id: str = Depends(get_current_user_id)) -> UserProfile:
    data = _fetch_user_with_profile(user_id)
    return UserProfile(**data)


@router.patch("/me", response_model=UserProfile)
async def update_me(
    body: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
) -> UserProfile:
    db = get_db()

    # Filtra apenas campos enviados (não sobrescreve com None)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        result = db.table("profiles").update(updates).eq("user_id", user_id).execute()
        if not result.data:
            # Perfil pode não existir se foi criado antes do trigger — cria agora
            db.table("profiles").insert({"user_id": user_id, **updates}).execute()

    return UserProfile(**_fetch_user_with_profile(user_id))


@router.delete("/me", response_model=MessageResponse)
async def delete_me(user_id: str = Depends(get_current_user_id)) -> MessageResponse:
    """Deleção suave: remove dados pessoais mas mantém registro para auditoria."""
    db = get_db()
    db.table("profiles").delete().eq("user_id", user_id).execute()
    db.table("users").update({
        "email": f"deleted_{user_id}@deleted",
        "password_hash": "DELETED",
        "full_name": "Conta deletada",
        "email_confirm_token": None,
    }).eq("id", user_id).execute()
    return MessageResponse(message="Conta removida com sucesso.")
