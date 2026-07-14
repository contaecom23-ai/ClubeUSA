"""
Operações de perfil de usuário.

ISOLAMENTO MULTI-TENANT:
  - user_id vem SEMPRE do token JWT (validado em deps.py)
  - NUNCA aceitar user_id do corpo da request
  - Busca de outro user retorna 404 (não vazar existência)
"""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.database import get_admin_client
from app.users.schemas import ProfileResponse, ProfileUpdateRequest


def _row_to_profile(row: dict, email: str) -> ProfileResponse:
    return ProfileResponse(
        id=row["id"],
        email=email,
        full_name=row["full_name"],
        city=row.get("city"),
        state=row.get("state"),
        phone=row.get("phone"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_my_profile(user_id: str, email: str) -> ProfileResponse:
    client = get_admin_client()
    resp = (
        client.table("profiles")
        .select("*")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Perfil não encontrado.")
    return _row_to_profile(resp.data, email)


def update_my_profile(
    user_id: str, email: str, updates: ProfileUpdateRequest
) -> ProfileResponse:
    payload = updates.model_dump(exclude_none=True)
    if not payload:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="Nenhum campo para atualizar.")

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()

    client = get_admin_client()
    resp = (
        client.table("profiles")
        .update(payload)
        .eq("id", user_id)        # SEMPRE filtrar por user_id do token
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Perfil não encontrado.")
    return _row_to_profile(resp.data[0], email)
