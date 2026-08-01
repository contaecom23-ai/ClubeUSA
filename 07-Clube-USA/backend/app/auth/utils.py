import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from ..config import get_settings

# pbkdf2_sha256: NIST-approved, no 72-byte limit, uses stdlib hashlib
# Migração futura para argon2 é possível adicionando-o como scheme principal e
# deixando pbkdf2_sha256 como deprecated — passlib verifica e reencripta no login.
_pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_ctx.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    s = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=s.access_token_expire_minutes)
    payload = {"sub": user_id, "exp": expire, "type": "access"}
    return jwt.encode(payload, s.secret_key, algorithm=s.algorithm)


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def decode_access_token(token: str) -> str:
    """Decodifica e valida o access token. Retorna user_id ou lança JWTError."""
    s = get_settings()
    payload = jwt.decode(token, s.secret_key, algorithms=[s.algorithm])
    if payload.get("type") != "access":
        raise JWTError("tipo de token inválido")
    user_id: str | None = payload.get("sub")
    if not user_id:
        raise JWTError("sub ausente")
    return user_id


def generate_email_token() -> str:
    return secrets.token_urlsafe(32)
