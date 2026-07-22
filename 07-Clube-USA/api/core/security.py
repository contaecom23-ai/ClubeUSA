"""
Segurança: hash de senha (bcrypt nativo) + JWT (HMAC-SHA256 via stdlib).
Evita dependência da biblioteca `cryptography` (que tem problemas em alguns ambientes).
"""
import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any, Dict, Optional

import bcrypt

from .config import settings


# ─── Senhas ───────────────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ─── JWT HMAC-SHA256 (sem dependência externa) ────────────────────────────────

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    # Repadding
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


def _sign(header_b64: str, payload_b64: str, secret: str) -> str:
    msg = f"{header_b64}.{payload_b64}".encode("ascii")
    sig = hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).digest()
    return _b64url_encode(sig)


def _encode_jwt(payload: Dict[str, Any]) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    sig = _sign(header, body, settings.SECRET_KEY)
    return f"{header}.{body}.{sig}"


def _decode_jwt_verified(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Token malformado.")
    header_b64, body_b64, sig = parts

    expected_sig = _sign(header_b64, body_b64, settings.SECRET_KEY)
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Assinatura inválida.")

    payload = json.loads(_b64url_decode(body_b64))
    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expirado.")

    return payload


# ─── API pública ──────────────────────────────────────────────────────────────

class JWTError(Exception):
    pass


def create_access_token(user_id: str) -> str:
    exp = int(time.time()) + settings.ACCESS_TOKEN_TTL_SECONDS
    return _encode_jwt({"sub": user_id, "exp": exp, "type": "access"})


def create_refresh_token(user_id: str) -> str:
    exp = int(time.time()) + settings.REFRESH_TOKEN_TTL_SECONDS
    return _encode_jwt({"sub": user_id, "exp": exp, "type": "refresh"})


def decode_jwt(token: str) -> Dict[str, Any]:
    try:
        return _decode_jwt_verified(token)
    except (ValueError, KeyError, json.JSONDecodeError, Exception) as exc:
        raise JWTError(str(exc)) from exc


def generate_opaque_token() -> str:
    return secrets.token_urlsafe(32)
