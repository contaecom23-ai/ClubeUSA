import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import get_settings


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── Tokens ───────────────────────────────────────────────────────────────────

def generate_opaque_token(nbytes: int = 48) -> str:
    """URL-safe random token (not a JWT) — used for email verification + refresh."""
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """SHA-256 hash of a token for safe storage."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str) -> tuple[str, int]:
    """Returns (jwt_string, expires_in_seconds)."""
    s = get_settings()
    expire_seconds = s.jwt_access_token_expire_minutes * 60
    payload = {
        "sub": user_id,
        "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expire_seconds),
        "iat": datetime.now(tz=timezone.utc),
        "type": "access",
    }
    token = jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)
    return token, expire_seconds


def decode_access_token(token: str) -> str:
    """Returns user_id (sub) or raises jose.JWTError."""
    s = get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload["sub"]


def refresh_token_expiry() -> datetime:
    s = get_settings()
    return datetime.now(tz=timezone.utc) + timedelta(days=s.jwt_refresh_token_expire_days)
