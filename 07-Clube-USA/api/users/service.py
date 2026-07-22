from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


async def get_user(db: AsyncSession, user_id: str) -> User:
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    return user


async def update_profile(
    db: AsyncSession,
    user_id: str,
    full_name: str | None,
    zip_code: str | None,
    us_state: str | None,
    bio: str | None,
) -> User:
    user = await get_user(db, user_id)

    # Apenas atualiza campos explicitamente enviados (None = não alterar)
    if full_name is not None:
        user.full_name = full_name
    if zip_code is not None:
        user.zip_code = zip_code
    if us_state is not None:
        user.us_state = us_state
    if bio is not None:
        user.bio = bio

    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    return user
