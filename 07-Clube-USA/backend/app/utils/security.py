"""
Utilitários de segurança.

Observação de compatibilidade: passlib 1.7.4 é incompatível com bcrypt 5.0.0
(o detect_wrap_bug interno envia >72 bytes, que o bcrypt 5.0 rejeita com ValueError).
Usamos bcrypt diretamente com pré-hash SHA-256 (digest = 64 bytes, < limite 72 do bcrypt).
Pré-hash é prática estabelecida: https://security.stackexchange.com/a/6627
"""
import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.utils.jwt_hs256 import encode as jwt_encode, decode as jwt_decode, JWTError
from app.config import settings


def _prehash(password: str) -> bytes:
    """SHA-256 hex digest → 64 bytes ASCII, dentro do limite de 72 do bcrypt."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest().encode("ascii")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prehash(password), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(_prehash(plain), hashed.encode("utf-8"))


def generate_token(n_bytes: int = 32) -> str:
    """Gera token URL-safe aleatório (confirmação de email, refresh token, etc.)."""
    return secrets.token_urlsafe(n_bytes)


def hash_token(token: str) -> str:
    """SHA-256 do token — armazenamos só o hash no banco."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: str) -> tuple[str, datetime]:
    """Cria JWT HS256 de acesso com TTL de ACCESS_TOKEN_EXPIRE_DAYS."""
    expires = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": int(expires.timestamp()),
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "type": "access",
    }
    token = jwt_encode(payload, settings.SECRET_KEY)
    return token, expires


def decode_access_token(token: str) -> Optional[str]:
    """Decodifica JWT de acesso; retorna user_id ou None se inválido/expirado."""
    try:
        payload = jwt_decode(token, settings.SECRET_KEY)
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None
