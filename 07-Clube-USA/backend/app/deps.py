from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.db import get_db
from app.security import decode_access_token

_bearer = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(_bearer)) -> dict:
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(status_code=401, detail="Token invalido ou expirado")

    db = get_db()
    result = db.table("users").select(
        "id,email,full_name,zip_code,city,state,phone,bio,avatar_url,email_confirmed,created_at,last_login_at"
    ).eq("id", user_id).eq("is_active", True).execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Usuario nao encontrado")

    return result.data[0]
