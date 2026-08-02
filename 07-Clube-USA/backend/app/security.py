import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

_pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> tuple[str, datetime]:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=settings.access_token_ttl_days)
    payload: dict[str, Any] = {"sub": user_id, "exp": expires}
    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token, expires


def decode_access_token(token: str) -> str:
    """Retorna user_id ou levanta JWTError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise JWTError("sub ausente")
    return user_id


# ── Email confirmation tokens ─────────────────────────────────────────────────

def generate_email_token() -> str:
    return secrets.token_urlsafe(32)
