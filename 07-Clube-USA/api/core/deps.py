"""Dependências injetadas nos endpoints FastAPI."""
from typing import AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .security import JWTError, decode_jwt

bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> str:
    """Valida o JWT e retorna o user_id (sub). Lança 401 em qualquer erro."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_jwt(credentials.credentials)
        if payload.get("type") != "access":
            raise exc
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise exc
        return user_id
    except JWTError:
        raise exc
