import base64
import hashlib
import hmac
import json
import os
import time
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_security = HTTPBearer()


def _b64url_decode(data: str) -> bytes:
    remainder = len(data) % 4
    if remainder:
        data += "=" * (4 - remainder)
    return base64.urlsafe_b64decode(data)


def _verify_hs256_jwt(token: str, secret: str) -> dict:
    """Verifica JWT HS256 usando stdlib (sem dependência externa).

    Supabase emite tokens HS256 assinados com o JWT Secret do projeto.
    """
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Formato JWT inválido")

    header_b64, payload_b64, sig_b64 = parts

    # Verifica assinatura com compare_digest (anti timing-attack)
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected_sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    actual_sig = _b64url_decode(sig_b64)
    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Assinatura inválida")

    payload = json.loads(_b64url_decode(payload_b64))

    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expirado")

    if payload.get("aud") != "authenticated":
        raise ValueError("Audience inválido")

    return payload


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(_security),
) -> dict:
    """Verifica JWT emitido pelo Supabase Auth e retorna {user_id, email}.

    O user_id é extraído do token no servidor — nunca aceito do cliente.
    """
    secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET não configurado")

    try:
        payload = _verify_hs256_jwt(credentials.credentials, secret)
    except ValueError as exc:
        detail = "Token expirado" if "expirado" in str(exc) else "Token inválido"
        raise HTTPException(status_code=401, detail=detail)

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token sem subject")

    return {"user_id": user_id, "email": payload.get("email", "")}
