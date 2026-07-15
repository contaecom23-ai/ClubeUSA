"""
Implementação mínima de JWT HS256 usando apenas built-ins do Python.
Motivo: a versão do pacote 'cryptography' disponível neste ambiente tem
um binding Rust/CFFI quebrado que impede o uso de python-jose e PyJWT.
HS256 = HMAC-SHA256 — disponível em stdlib (hmac + hashlib).
"""
import base64
import hashlib
import hmac
import json
import time
from typing import Any, Optional


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64_decode(s: str) -> bytes:
    # Repadding necessário antes de decodificar
    pad = 4 - len(s) % 4
    if pad != 4:
        s += "=" * pad
    return base64.urlsafe_b64decode(s)


_HEADER = _b64_encode(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())


def encode(payload: dict[str, Any], secret: str) -> str:
    body = _b64_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{_HEADER}.{body}"
    sig = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64_encode(sig)}"


class JWTError(Exception):
    pass


def decode(token: str, secret: str) -> dict[str, Any]:
    """Decodifica e valida JWT. Levanta JWTError em caso de falha."""
    parts = token.split(".")
    if len(parts) != 3:
        raise JWTError("Formato inválido")

    header_b64, body_b64, sig_b64 = parts
    signing_input = f"{header_b64}.{body_b64}"

    expected_sig = hmac.new(
        secret.encode(),
        signing_input.encode(),
        hashlib.sha256,
    ).digest()

    try:
        provided_sig = _b64_decode(sig_b64)
    except Exception:
        raise JWTError("Assinatura inválida")

    if not hmac.compare_digest(expected_sig, provided_sig):
        raise JWTError("Assinatura inválida")

    try:
        payload = json.loads(_b64_decode(body_b64))
    except Exception:
        raise JWTError("Payload inválido")

    # Validar expiração
    exp = payload.get("exp")
    if exp is not None and int(time.time()) > exp:
        raise JWTError("Token expirado")

    return payload
