import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from .config import settings


# ── Passwords ─────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT access tokens ─────────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


# ── Refresh tokens (armazena hash, nunca o token bruto) ──────────────────────

def create_refresh_token() -> tuple[str, str]:
    """Retorna (token_bruto, token_hash). Só o hash vai para o banco."""
    token = secrets.token_urlsafe(40)
    token_hash = _sha256(token)
    return token, token_hash


def hash_refresh_token(token: str) -> str:
    return _sha256(token)


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


# ── Geração de códigos ────────────────────────────────────────────────────────

def generate_referral_code() -> str:
    """8 caracteres alfanuméricos maiúsculos. Colisão rara, tratada na camada de serviço."""
    return secrets.token_urlsafe(6)[:8].upper()


def generate_email_token() -> str:
    return secrets.token_urlsafe(40)
