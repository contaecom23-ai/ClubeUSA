"""
Lógica de negócio de autenticação.
Regras de segurança:
  - user_id vem SEMPRE do token JWT, nunca do body do request.
  - Acesso a recurso de outro usuário retorna 404 (não vazar existência).
  - Nunca logar senhas, tokens ou PII.
"""
from datetime import datetime, timezone

from fastapi import HTTPException
from supabase import AsyncClient

from app.email_service import send_confirmation_email
from app.security import (
    create_access_token,
    generate_confirmation_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.config import settings


async def register_user(db: AsyncClient, email: str, password: str, full_name: str) -> str:
    email = email.lower().strip()

    # Verificar se email já existe (retorna 400, não 404, pois é erro de input)
    existing = await db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    pwd_hash = hash_password(password)
    confirmation_token, confirmation_expires = generate_confirmation_token()

    # Inserir usuário
    result = await db.table("users").insert({
        "email": email,
        "password_hash": pwd_hash,
        "full_name": full_name,
        "email_confirmation_token": confirmation_token,
        "email_confirmation_expires_at": confirmation_expires.isoformat(),
    }).execute()

    user = result.data[0]
    user_id = user["id"]

    # Criar perfil vazio (1:1 com users)
    await db.table("profiles").insert({"user_id": user_id}).execute()

    # Enviar email (falha aqui não desfaz o cadastro — aceitar e deixar reenvio futuro)
    try:
        await send_confirmation_email(email, full_name, confirmation_token)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Erro ao enviar email de confirmação para %s", email)

    return "Cadastro realizado! Verifique seu email para ativar a conta."


async def confirm_email(db: AsyncClient, token: str) -> str:
    result = await db.table("users") \
        .select("id, email_confirmation_expires_at, email_confirmed") \
        .eq("email_confirmation_token", token) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado")

    user = result.data[0]

    if user["email_confirmed"]:
        return "Email já confirmado"

    expires_at = datetime.fromisoformat(user["email_confirmation_expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo email de confirmação.")

    await db.table("users").update({
        "email_confirmed": True,
        "email_confirmation_token": None,
        "email_confirmation_expires_at": None,
    }).eq("id", user["id"]).execute()

    return "Email confirmado com sucesso! Você já pode fazer login."


async def login_user(db: AsyncClient, email: str, password: str) -> dict:
    email = email.lower().strip()

    result = await db.table("users") \
        .select("id, password_hash, email_confirmed, is_active") \
        .eq("email", email) \
        .execute()

    # Mensagem genérica intencionalmente — não revelar se o email existe
    if not result.data:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    user = result.data[0]

    if not verify_password(password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")

    if not user["is_active"]:
        raise HTTPException(status_code=403, detail="Conta desativada. Entre em contato com o suporte.")

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=403,
            detail="Email não confirmado. Verifique sua caixa de entrada."
        )

    user_id = user["id"]
    access_token, _ = create_access_token(user_id)
    refresh_plaintext, refresh_hash, refresh_expires = generate_refresh_token()

    await db.table("refresh_tokens").insert({
        "user_id": user_id,
        "token_hash": refresh_hash,
        "expires_at": refresh_expires.isoformat(),
    }).execute()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_days": settings.ACCESS_TOKEN_EXPIRE_DAYS,
        "refresh_token": refresh_plaintext,
    }


async def refresh_session(db: AsyncClient, refresh_token_plain: str) -> dict:
    token_hash = hash_refresh_token(refresh_token_plain)

    result = await db.table("refresh_tokens") \
        .select("id, user_id, expires_at, used_at") \
        .eq("token_hash", token_hash) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    rt = result.data[0]

    if rt["used_at"] is not None:
        raise HTTPException(status_code=401, detail="Refresh token já utilizado")

    expires_at = datetime.fromisoformat(rt["expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Refresh token expirado. Faça login novamente.")

    # Invalidar token atual (rotação)
    await db.table("refresh_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", rt["id"]).execute()

    user_id = rt["user_id"]
    access_token, _ = create_access_token(user_id)
    new_refresh_plain, new_refresh_hash, new_refresh_expires = generate_refresh_token()

    await db.table("refresh_tokens").insert({
        "user_id": user_id,
        "token_hash": new_refresh_hash,
        "expires_at": new_refresh_expires.isoformat(),
    }).execute()

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_days": settings.ACCESS_TOKEN_EXPIRE_DAYS,
        "refresh_token": new_refresh_plain,
    }


async def logout_user(db: AsyncClient, refresh_token_plain: str) -> None:
    token_hash = hash_refresh_token(refresh_token_plain)
    await db.table("refresh_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat(),
    }).eq("token_hash", token_hash).execute()
