from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.middleware import get_current_user
from app.profile.schemas import ProfileResponse, ProfileUpdate
from app.profile.service import get_profile, upsert_profile

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def read_profile(user: dict = Depends(get_current_user)):
    """Retorna o perfil do usuário autenticado."""
    user_id: str = user["sub"]
    profile = get_profile(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Perfil não encontrado. Complete seu cadastro.",
        )
    return profile


@router.put("", response_model=ProfileResponse)
def update_profile(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    """Atualiza o perfil do usuário autenticado.

    - user_id vem do JWT (nunca do body) → sem risco de IDOR.
    - Campos omitidos/None não sobrescrevem valores existentes.
    """
    user_id: str = user["sub"]
    updated = upsert_profile(user_id, body.model_dump())
    return updated
