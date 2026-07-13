import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

# Argon2id — recommended by OWASP, winner of PHC; better than bcrypt for modern hardware
_ph = PasswordHasher()
ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def create_access_token(user_id: str, expire_minutes: int = 60 * 24 * 7) -> str:
    from app.config import get_settings
    s = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": exp, "type": "access"},
        s.secret_key,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> Optional[str]:
    from app.config import get_settings
    s = get_settings()
    try:
        payload = jwt.decode(token, s.secret_key, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw_token, sha256_hash). Store only the hash."""
    raw = secrets.token_urlsafe(64)
    return raw, _hash_token(raw)


def hash_refresh_token(raw: str) -> str:
    return _hash_token(raw)


def generate_confirmation_token() -> str:
    return secrets.token_urlsafe(32)


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
