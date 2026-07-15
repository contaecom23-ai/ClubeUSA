"""
Rotas protegidas de perfil do usuário.
O user_id vem SEMPRE do JWT (servidor), nunca do body do cliente.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from supabase import AsyncClient

from app.database import get_db
from app.security import get_current_user_id

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None
    phone: Optional[str] = None


def _safe_user(user: dict) -> dict:
    """Remove campos sensíveis antes de retornar ao cliente."""
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "zip_code": user.get("zip_code"),
        "phone": user.get("phone"),
        "email_confirmed": user["email_confirmed"],
        "created_at": user["created_at"],
    }


@router.get("/me")
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncClient = Depends(get_db),
):
    res = (
        await db.table("users")
        .select("id,email,full_name,zip_code,phone,email_confirmed,created_at")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return res.data


@router.patch("/me")
async def update_profile(
    body: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncClient = Depends(get_db),
):
    updates: dict = {}
    if body.full_name is not None:
        name = body.full_name.strip()
        if len(name) < 2:
            raise HTTPException(status_code=400, detail="Nome inválido.")
        updates["full_name"] = name
    if body.zip_code is not None:
        updates["zip_code"] = body.zip_code.strip() or None
    if body.phone is not None:
        updates["phone"] = body.phone.strip() or None

    if not updates:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    res = (
        await db.table("users")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _safe_user(res.data[0])
