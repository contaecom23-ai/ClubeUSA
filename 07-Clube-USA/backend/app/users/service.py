"""
Lógica de perfil de usuário.
Regra crítica: user_id vem SEMPRE do JWT (get_current_user_id).
Nunca usar ID do body/path sem verificar ownership — retornar 404 se não pertencer.
"""
from fastapi import HTTPException
from supabase import AsyncClient


async def get_me(db: AsyncClient, user_id: str) -> dict:
    user_result = await db.table("users") \
        .select("id, email, full_name, email_confirmed") \
        .eq("id", user_id) \
        .execute()

    if not user_result.data:
        raise HTTPException(status_code=404, detail="Not found")

    user = user_result.data[0]

    profile_result = await db.table("profiles") \
        .select("zip_code, city, state_code, phone, bio, avatar_url") \
        .eq("user_id", user_id) \
        .execute()

    profile = profile_result.data[0] if profile_result.data else None

    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "email_confirmed": user["email_confirmed"],
        "profile": profile,
    }


async def update_profile(db: AsyncClient, user_id: str, updates: dict) -> dict:
    # Filtrar campos None (não sobrescrever com null)
    non_null = {k: v for k, v in updates.items() if v is not None}

    if non_null:
        await db.table("profiles").update(non_null).eq("user_id", user_id).execute()

    profile_result = await db.table("profiles") \
        .select("zip_code, city, state_code, phone, bio, avatar_url") \
        .eq("user_id", user_id) \
        .execute()

    return profile_result.data[0] if profile_result.data else {}
