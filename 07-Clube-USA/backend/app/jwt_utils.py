"""
Minimal HS256 JWT implementation using only Python builtins.
Avoids the cryptography/cffi dependency that breaks in some environments.
Conforms to RFC 7519 for HS256 (HMAC-SHA256).
"""
import base64
import hashlib
import hmac
import json
import time
import uuid
from datetime import datetime, timedelta, timezone


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * (pad % 4))


def encode(payload: dict, secret: str) -> str:
    header = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64url_encode(json.dumps(payload, separators=(",", ":"), default=_json_default).encode())
    sig_input = f"{header}.{body}".encode()
    sig = _b64url_encode(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
    return f"{header}.{body}.{sig}"


def decode(token: str, secret: str) -> dict:
    """Verify and decode. Raises ValueError on any failure."""
    try:
        header_b64, body_b64, sig_b64 = token.split(".")
    except ValueError:
        raise ValueError("Malformed token")

    # Verify signature
    sig_input = f"{header_b64}.{body_b64}".encode()
    expected = _b64url_encode(hmac.new(secret.encode(), sig_input, hashlib.sha256).digest())
    if not hmac.compare_digest(expected, sig_b64):
        raise ValueError("Invalid signature")

    payload = json.loads(_b64url_decode(body_b64))

    # Check expiry
    exp = payload.get("exp")
    if exp and int(time.time()) > exp:
        raise ValueError("Token expired")

    return payload


def _json_default(obj):
    if isinstance(obj, datetime):
        return int(obj.timestamp())
    raise TypeError(f"Not serializable: {type(obj)}")


def make_access_token(user_id: str, secret: str, expire_days: int) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + expire_days * 86400,
        "jti": str(uuid.uuid4()),
    }
    return encode(payload, secret)
