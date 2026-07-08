from fastapi import APIRouter, Depends, HTTPException

from ..database import get_supabase
from ..middleware.auth import get_current_user_id
from ..models.user import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/profile", tags=["profile"])


def _build_profile_response(user_id: str) -> ProfileResponse:
    db = get_supabase()

    profile_resp = (
        db.table("profiles").select("*").eq("id", user_id).maybe_single().execute()
    )
    if not profile_resp.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    user_resp = db.auth.admin.get_user_by_id(user_id)
    if not user_resp.user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    p = profile_resp.data
    u = user_resp.user

    return ProfileResponse(
        id=user_id,
        full_name=p["full_name"],
        email=u.email,
        zip_code=p.get("zip_code"),
        state_us=p.get("state_us"),
        city=p.get("city"),
        whatsapp=p.get("whatsapp"),
        email_confirmed=u.email_confirmed_at is not None,
        created_at=str(p["created_at"]),
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user_id)):
    return _build_profile_response(user_id)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    body: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
):
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    db = get_supabase()
    result = db.table("profiles").update(update_data).eq("id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    return _build_profile_response(user_id)
