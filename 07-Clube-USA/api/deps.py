from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from database import get_supabase_client
from security import decode_access_token

_bearer = HTTPBearer(auto_error=True)


def get_db() -> Client:
    """FastAPI dependency: retorna o cliente Supabase (service_role)."""
    return get_supabase_client()


async def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> str:
    """FastAPI dependency: valida Bearer token e retorna user_id."""
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
