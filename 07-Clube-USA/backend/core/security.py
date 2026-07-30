import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ── Password ──────────────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


# ── JWT (access tokens only) ──────────────────────────────────────────────────

ALGORITHM = "HS256"


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=settings.access_token_ttl),
        "type": "access",
    }
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Return user_id or raise JWTError."""
    payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("wrong token type")
    sub = payload.get("sub")
    if not sub:
        raise JWTError("missing sub")
    return sub


# ── Refresh tokens (opaque, stored as SHA-256 hash) ───────────────────────────

def generate_refresh_token() -> str:
    """Return a high-entropy URL-safe token (never stored plaintext)."""
    return secrets.token_urlsafe(32)


def hash_token(raw: str) -> str:
    """SHA-256 hex digest — what gets stored in the DB."""
    return hashlib.sha256(raw.encode()).hexdigest()


def refresh_token_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.refresh_token_ttl)


# ── Email confirmation tokens ─────────────────────────────────────────────────

def generate_email_confirm_token() -> str:
    return secrets.token_urlsafe(32)


def email_confirm_expires_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=settings.email_confirm_ttl)
