from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import ProfileUpdateRequest


async def update_profile(db: AsyncSession, user: User, data: ProfileUpdateRequest) -> User:
    updates = data.model_dump(exclude_none=True)
    for field, value in updates.items():
        setattr(user, field, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
