from app.db import get_db

SAFE_PROFILE_FIELDS = "id,email,full_name,zip_code,city,state,phone,bio,avatar_url,email_confirmed,created_at,last_login_at"


def get_user_by_id(user_id: str) -> dict | None:
    db = get_db()
    result = db.table("users").select(SAFE_PROFILE_FIELDS).eq("id", user_id).eq("is_active", True).execute()
    return result.data[0] if result.data else None


def update_user_profile(user_id: str, fields: dict) -> dict:
    db = get_db()
    # Whitelist: only these fields can be updated by the user
    allowed = {"full_name", "zip_code", "city", "state", "phone", "bio"}
    safe = {k: v for k, v in fields.items() if k in allowed}

    if not safe:
        # Nothing to update — just return current profile
        return get_user_by_id(user_id)

    result = db.table("users").update(safe).eq("id", user_id).execute()
    return result.data[0] if result.data else get_user_by_id(user_id)
