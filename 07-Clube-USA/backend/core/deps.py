from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import Client
from .supabase_client import get_supabase

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    supabase: Annotated[Client, Depends(get_supabase)],
) -> dict:
    token = credentials.credentials
    try:
        res = supabase.auth.admin.get_user(token)
        user = res.user
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        return {
            "id": str(user.id),
            "email": user.email,
            "email_confirmed_at": user.email_confirmed_at,
        }
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")


async def get_confirmed_user(
    current_user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    if not current_user.get("email_confirmed_at"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )
    return current_user
