import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import jwt
from supabase import Client

from ..config import get_settings

# Pre-computed bcrypt hash used for timing-safe dummy verification
# (prevents user-enumeration via response-time differences).
_DUMMY_HASH: bytes = b"$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")


def _gen_confirmation_token() -> tuple[str, datetime]:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.CONFIRMATION_TOKEN_EXPIRE_HOURS
    )
    return token, expires_at


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(
    db: Client, email: str, password: str, full_name: str, zip_code: str
) -> tuple[dict, str]:
    """Create user + profile. Returns (user_row, confirmation_token)."""
    email = email.lower().strip()

    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está cadastrado",
        )

    token, expires_at = _gen_confirmation_token()

    user_result = db.table("users").insert({
        "email": email,
        "password_hash": hash_password(password),
        "email_confirmed": False,
        "email_confirmation_token": token,
        "email_confirmation_expires_at": expires_at.isoformat(),
    }).execute()

    user = user_result.data[0]
    user_id = user["id"]

    db.table("profiles").insert({
        "user_id": user_id,
        "full_name": full_name.strip(),
        "zip_code": zip_code,
    }).execute()

    return user, token


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(db: Client, email: str, password: str) -> dict:
    email = email.lower().strip()
    result = (
        db.table("users")
        .select("id, email, password_hash, email_confirmed, is_active")
        .eq("email", email)
        .execute()
    )

    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha inválidos",
    )

    if not result.data:
        # Timing-safe: still run bcrypt to prevent enumeration via timing
        bcrypt.checkpw(password.encode(), _DUMMY_HASH)
        raise invalid

    user = result.data[0]

    if not verify_password(password, user["password_hash"]):
        raise invalid

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )

    return user


# ── Email confirmation ────────────────────────────────────────────────────────

def confirm_email(db: Client, token: str) -> None:
    result = (
        db.table("users")
        .select("id, email_confirmed, email_confirmation_expires_at")
        .eq("email_confirmation_token", token)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado",
        )

    user = result.data[0]

    if user["email_confirmed"]:
        return  # Idempotent

    expires_raw = user["email_confirmation_expires_at"]
    if expires_raw:
        expires_at = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token expirado. Solicite um novo link de confirmação.",
            )

    db.table("users").update({
        "email_confirmed": True,
        "email_confirmation_token": None,
        "email_confirmation_expires_at": None,
    }).eq("id", user["id"]).execute()


# ── Resend confirmation ───────────────────────────────────────────────────────

def resend_confirmation(db: Client, email: str) -> tuple[str, str] | None:
    """Return (new_token, user_id) or None (email not found / already confirmed)."""
    email = email.lower().strip()
    result = (
        db.table("users")
        .select("id, email_confirmed")
        .eq("email", email)
        .execute()
    )

    if not result.data:
        return None

    user = result.data[0]
    if user["email_confirmed"]:
        return None

    token, expires_at = _gen_confirmation_token()
    db.table("users").update({
        "email_confirmation_token": token,
        "email_confirmation_expires_at": expires_at.isoformat(),
    }).eq("id", user["id"]).execute()

    return token, user["id"]
