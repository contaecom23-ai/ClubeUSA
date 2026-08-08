"""
Lógica de negócio para autenticação.
Toda query usa o service_role client — dado nunca vem do input do cliente.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from supabase import Client

from app.auth.security import (
    confirm_token_expires_at,
    create_access_token,
    generate_confirm_token,
    hash_password,
    verify_password,
)
from app.config import get_settings
from app.email_service import build_confirmation_email, send_email

logger = logging.getLogger(__name__)

# Janela e limite de rate-limit por IP para registro/login
RATE_LIMIT_WINDOW_MINUTES = 15
RATE_LIMIT_MAX_ATTEMPTS = 10


# ---------------------------------------------------------------
# Rate limit
# ---------------------------------------------------------------

async def check_rate_limit(db: Client, key: str) -> None:
    """Levanta 429 se a chave excedeu o limite na janela."""
    window_start = datetime.now(timezone.utc).replace(microsecond=0)
    cutoff = f"NOW() - INTERVAL '{RATE_LIMIT_WINDOW_MINUTES} minutes'"

    result = (
        db.table("rate_limits")
        .select("id", count="exact")
        .eq("key", key)
        .gte("created_at", f"NOW() - INTERVAL '{RATE_LIMIT_WINDOW_MINUTES} minutes'")
        .execute()
    )
    # supabase-py retorna count em result.count
    count = result.count or 0
    if count >= RATE_LIMIT_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Muitas tentativas. Aguarde {RATE_LIMIT_WINDOW_MINUTES} minutos.",
        )
    db.table("rate_limits").insert({"key": key}).execute()


# ---------------------------------------------------------------
# Registro
# ---------------------------------------------------------------

async def register_user(db: Client, email: str, password: str, full_name: str, client_ip: str) -> dict:
    await check_rate_limit(db, f"register:{client_ip}")

    email = email.lower().strip()

    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        # Retorna 409, mas com mensagem genérica para não vazar existência do email
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar a conta. Verifique os dados e tente novamente.",
        )

    token = generate_confirm_token()
    expires_at = confirm_token_expires_at()

    user_data = {
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name.strip(),
        "email_confirm_token": token,
        "email_confirm_expires_at": expires_at.isoformat(),
        "email_confirmed": False,
    }

    result = db.table("users").insert(user_data).execute()
    user = result.data[0]

    s = get_settings()
    confirm_url = f"{s.app_url}/auth/confirm-email?token={token}"
    subject, html = build_confirmation_email(full_name.strip(), confirm_url)
    await send_email(email, subject, html)

    return user


# ---------------------------------------------------------------
# Confirmação de email
# ---------------------------------------------------------------

def confirm_email(db: Client, token: str) -> dict:
    result = (
        db.table("users")
        .select("id, email_confirmed, email_confirm_expires_at")
        .eq("email_confirm_token", token)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token inválido.")

    user = result.data[0]

    if user["email_confirmed"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email já confirmado.")

    expires_at = datetime.fromisoformat(user["email_confirm_expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Faça login e solicite um novo link.",
        )

    db.table("users").update(
        {
            "email_confirmed": True,
            "email_confirm_token": None,
            "email_confirm_expires_at": None,
        }
    ).eq("id", user["id"]).execute()

    return {"id": user["id"]}


# ---------------------------------------------------------------
# Login
# ---------------------------------------------------------------

async def login_user(db: Client, email: str, password: str, client_ip: str) -> str:
    await check_rate_limit(db, f"login:{client_ip}")

    email = email.lower().strip()

    result = (
        db.table("users")
        .select("id, password_hash, email_confirmed, is_active")
        .eq("email", email)
        .execute()
    )

    # Resposta genérica para não revelar se o email existe
    invalid_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email ou senha incorretos.",
    )

    if not result.data:
        raise invalid_exc

    user = result.data[0]

    if not verify_password(password, user["password_hash"]):
        raise invalid_exc

    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada.")

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    return create_access_token(user["id"])
