from fastapi import APIRouter, Depends, HTTPException, status

from .. import database as db
from ..deps import current_user_id
from ..schemas import UpdateProfileRequest, UserProfile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_profile(user_id: str = Depends(current_user_id)):
    user = await db.fetchrow(
        """
        SELECT id, email, full_name, phone, zip_code, city, state, country,
               email_confirmed, referral_code, created_at, last_login_at
        FROM users
        WHERE id = $1 AND is_active = TRUE
        """,
        user_id,
    )
    if not user:
        # user_id veio do token mas não existe mais → 404 (não vazar que foi deletado)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return dict(user)


@router.patch("/me", response_model=UserProfile)
async def update_profile(body: UpdateProfileRequest, user_id: str = Depends(current_user_id)):
    # Apenas campos enviados (não-None) são atualizados
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Nenhum campo para atualizar.")

    # Construir query dinâmica com parâmetros (seguro contra SQL injection)
    set_clauses = []
    values = []
    for i, (key, val) in enumerate(updates.items(), start=1):
        set_clauses.append(f"{key} = ${i}")
        values.append(val)

    values.append(user_id)
    query = f"""
        UPDATE users
        SET {', '.join(set_clauses)}
        WHERE id = ${len(values)} AND is_active = TRUE
        RETURNING id, email, full_name, phone, zip_code, city, state, country,
                  email_confirmed, referral_code, created_at, last_login_at
    """

    updated = await db.fetchrow(query, *values)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return dict(updated)
