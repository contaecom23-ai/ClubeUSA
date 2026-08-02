import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from .config import settings

ALGORITHM = "HS256"

# Pre-computed dummy hash used for constant-time anti-enumeration checks.
# Generated once at startup; never changes at runtime.
_DUMMY_HASH = bcrypt.hashpw(b"clube-usa-dummy-constant", bcrypt.gensalt())


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def dummy_verify() -> None:
    """Timing-constant no-op used in anti-enumeration paths."""
    bcrypt.checkpw(b"dummy", _DUMMY_HASH)


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
