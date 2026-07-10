"""JWT creation and verification.

Tokens contain only the user id (sub) — never email, name, or role.
user_id is always read from the verified token, never from the request body.
TTL: ACCESS_TOKEN_EXPIRE_DAYS (default 7 days).
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from ..config import settings

_bearer_scheme = HTTPBearer(auto_error=True)


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    """Returns user_id string or None if token is invalid/expired."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(_bearer_scheme),
) -> str:
    """FastAPI dependency — extracts user_id from Bearer token."""
    user_id = decode_access_token(credentials.credentials)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
