import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"

# Pre-computed dummy hash to make login-not-found timing match login-wrong-password.
# Computed once at import time to avoid per-request overhead.
_DUMMY_HASH: str = pwd_context.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def verify_password_constant_time(plain: str, hashed: Optional[str]) -> bool:
    """Always runs bcrypt to prevent user-enumeration via timing."""
    if hashed is None:
        pwd_context.verify(plain, _DUMMY_HASH)
        return False
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {"sub": user_id, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)
