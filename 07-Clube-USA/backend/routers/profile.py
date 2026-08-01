from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from middleware.auth import get_current_user
from services.supabase_client import get_supabase

router = APIRouter()


class ProfileOut(BaseModel):
    id: str
    full_name: str
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    language: str = "pt"
    created_at: str
    updated_at: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None

    @field_validator("full_name")
    @classmethod
    def name_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("full_name não pode ser vazio")
        return v.strip() if v else v

    @field_validator("zip_code")
    @classmethod
    def zip_digits_only(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.replace("-", "").isdigit():
            raise ValueError("zip_code deve conter apenas dígitos")
        return v

    @field_validator("state")
    @classmethod
    def state_uppercase(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    @field_validator("language")
    @classmethod
    def language_allowed(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("pt", "en", "es"):
            raise ValueError("language deve ser pt, en ou es")
        return v


@router.get("/me", response_model=ProfileOut)
async def get_my_profile(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Retorna o perfil do usuário autenticado.
    user_id vem SEMPRE do token JWT — nunca do request body.
    Retorna 404 (não 403) para não vazar existência de outros perfis (IDOR prevention).
    """
    sb = get_supabase()
    result = (
        sb.table("user_profiles")
        .select("*")
        .eq("id", current_user["user_id"])
        .single()
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return result.data


@router.patch("/me", response_model=ProfileOut)
async def update_my_profile(
    body: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Atualiza campos opcionais do perfil.
    Apenas campos enviados são atualizados (PATCH semântico).
    """
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo fornecido para atualizar",
        )

    sb = get_supabase()
    result = (
        sb.table("user_profiles")
        .update(updates)
        .eq("id", current_user["user_id"])
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Perfil não encontrado")
    return result.data[0]
