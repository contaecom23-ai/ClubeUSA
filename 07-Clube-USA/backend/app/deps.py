from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import decode_access_token

bearer = HTTPBearer()


async def current_user_id(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    """Extrai o user_id do JWT. user_id vem SEMPRE do token (nunca do request body)."""
    user_id = decode_access_token(creds.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
