"""
JWT de acesso (15 min) + token de refresh aleatório (7 dias, armazenado no DB).
Tokens de e-mail também são aleatórios e armazenados como SHA-256 no DB.
Argon2id para hashing de senhas (mais seguro que bcrypt, sem problemas de
compatibilidade com versões de biblioteca).
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

_ph = PasswordHasher()
_DUMMY_HASH = _ph.hash("clubeusa-dummy-password-for-timing-attack-prevention")

bearer_scheme = HTTPBearer(auto_error=False)
ALGORITHM = "HS256"


# ── Senhas ─────────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def dummy_verify() -> None:
    """Executa verify mesmo sem usuário encontrado para prevenir timing attacks."""
    try:
        _ph.verify(_DUMMY_HASH, "not-the-real-password")
    except Exception:
        pass


# ── Access token (JWT curto) ────────────────────────────────────────────────────

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise JWTError("wrong token type")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    return payload["sub"]


# ── Refresh token (aleatório, armazenado no DB) ────────────────────────────────

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """SHA-256 do token para armazenar no DB sem expor o valor raw."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── E-mail confirmation token ──────────────────────────────────────────────────

def generate_email_token() -> str:
    return secrets.token_urlsafe(32)
