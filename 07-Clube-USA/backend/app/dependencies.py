from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from app.database import get_db
from app.security import decode_access_token

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Client = Depends(get_db),
) -> dict:
    """Validate Bearer token and return the authenticated user row.

    user_id always comes from the token (server-verified), never from the request body.
    """
    user_id = decode_access_token(credentials.credentials)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = (
        db.table("users")
        .select("id, email, is_email_verified")
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return result.data[0]
