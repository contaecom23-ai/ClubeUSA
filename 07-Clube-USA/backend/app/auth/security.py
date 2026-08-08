import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings

ALGORITHM = "HS256"
CONFIRM_TOKEN_TTL_HOURS = 24
_BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: str) -> str:
    s = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(days=s.access_token_ttl_days)
    return jwt.encode({"sub": user_id, "iat": now, "exp": exp}, s.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Optional[str]:
    s = get_settings()
    try:
        payload = jwt.decode(token, s.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def generate_confirm_token() -> str:
    return secrets.token_urlsafe(32)


def confirm_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=CONFIRM_TOKEN_TTL_HOURS)
