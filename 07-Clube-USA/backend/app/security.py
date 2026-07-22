"""
JWT, hashing de senha, geração de tokens.
Nenhum segredo hardcoded — tudo vem das env vars via settings.

Hashing: bcrypt com SHA-256 pré-hash (evita o limite de 72 bytes do bcrypt
e é padrão seguro adotado por Dropbox, Django 4.2+, etc.).
"""
import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

from app.config import settings


# ── Senhas ──────────────────────────────────────────────────────────────

def _preprocess_password(password: str) -> bytes:
    """SHA-256 → base64 antes do bcrypt; elimina limite de 72 bytes."""
    digest = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(digest)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(_preprocess_password(password), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_preprocess_password(plain), hashed.encode("utf-8"))


# ── Access Token (JWT) ───────────────────────────────────────────────────

def create_access_token(user_id: str) -> tuple[str, datetime]:
    expires = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expires,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, expires


def decode_access_token(token: str) -> Optional[str]:
    """Retorna user_id se o token for válido, None caso contrário."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── Refresh Token ────────────────────────────────────────────────────────

def generate_refresh_token() -> tuple[str, str, datetime]:
    """
    Retorna (token_plaintext, token_hash, expires_at).
    Armazenar apenas o hash no banco; devolver plaintext ao cliente.
    """
    token = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return token, token_hash, expires


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


# ── Confirmation Token ───────────────────────────────────────────────────

def generate_confirmation_token() -> tuple[str, datetime]:
    """Retorna (token, expires_at). TTL de 24 horas."""
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    return token, expires
