import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from fastapi import Cookie, HTTPException, status

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# A pre-computed bcrypt hash used for constant-time comparison when a user
# doesn't exist, preventing user-enumeration via timing attacks on login.
_DUMMY_HASH = bcrypt.hashpw(b"dummy-timing-sentinel", bcrypt.gensalt(rounds=12)).decode()


def _get_secret_key() -> str:
    key = os.environ.get("SECRET_KEY", "")
    if not key:
        raise RuntimeError(
            "SECRET_KEY env var must be set. "
            "Generate with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    return key


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def generate_confirmation_token() -> str:
    return secrets.token_urlsafe(32)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        _get_secret_key(),
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user_id(
    access_token: Optional[str] = Cookie(default=None),
) -> str:
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
        )
    user_id = decode_access_token(access_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
        )
    return user_id
