import secrets
from datetime import datetime, timedelta, timezone

import bcrypt as _bcrypt
from jose import JWTError, jwt

from config import get_settings

# Precomputed at import; used for constant-time comparison when user not found
# (avoids timing-based user enumeration)
_DUMMY_HASH: bytes = _bcrypt.hashpw(b"__dummy_seed__", _bcrypt.gensalt(rounds=12))


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode("utf-8"), _bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str | bytes) -> bool:
    try:
        hashed_b = hashed if isinstance(hashed, bytes) else hashed.encode("utf-8")
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed_b)
    except Exception:
        return False


def get_dummy_hash() -> bytes:
    return _DUMMY_HASH


def create_access_token(user_id: str) -> str:
    s = get_settings()
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=s.JWT_TTL_DAYS),
    }
    return jwt.encode(payload, s.JWT_SECRET, algorithm=s.JWT_ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Retorna user_id se token válido, None caso contrário."""
    s = get_settings()
    try:
        payload = jwt.decode(token, s.JWT_SECRET, algorithms=[s.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def generate_email_token() -> str:
    return secrets.token_urlsafe(32)


def email_token_expiry() -> datetime:
    s = get_settings()
    return datetime.now(timezone.utc) + timedelta(hours=s.EMAIL_TOKEN_TTL_HOURS)
