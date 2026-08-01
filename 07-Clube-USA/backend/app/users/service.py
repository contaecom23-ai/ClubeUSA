import asyncpg
from fastapi import HTTPException, status

from .schemas import UpdateProfileRequest, UserProfile


async def get_my_profile(user_id: str, db: asyncpg.Connection) -> UserProfile:
    row = await db.fetchrow(
        """
        SELECT id, email, name, estado, cidade, whatsapp,
               email_confirmed, created_at, last_login_at
        FROM users
        WHERE id = $1 AND is_active = TRUE
        """,
        user_id,
    )
    if not row:
        # 404 — não vaza existência de outros usuários
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="usuário não encontrado")

    return UserProfile(
        id=str(row["id"]),
        email=row["email"],
        name=row["name"],
        estado=row["estado"],
        cidade=row["cidade"],
        whatsapp=row["whatsapp"],
        email_confirmed=row["email_confirmed"],
        created_at=row["created_at"],
        last_login_at=row["last_login_at"],
    )


async def update_my_profile(
    user_id: str, data: UpdateProfileRequest, db: asyncpg.Connection
) -> UserProfile:
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        return await get_my_profile(user_id, db)

    set_clauses = ", ".join(f"{col} = ${i+2}" for i, col in enumerate(updates))
    values = list(updates.values())

    await db.execute(
        f"UPDATE users SET {set_clauses} WHERE id = $1 AND is_active = TRUE",
        user_id,
        *values,
    )
    return await get_my_profile(user_id, db)
