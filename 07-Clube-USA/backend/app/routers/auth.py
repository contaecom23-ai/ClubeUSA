"""
Rotas públicas de autenticação.
Rotas: register, login, confirm-email, refresh, resend-confirmation, logout.
"""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase import AsyncClient

from app.database import get_db
from app.email_service import send_confirmation_email
from app.security import (
    create_access_token,
    dummy_verify,
    generate_email_token,
    generate_refresh_token,
    get_current_user_id,
    hash_password,
    hash_token,
    verify_password,
)
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)

# ── Schemas ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: str = ""

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter no mínimo 8 caracteres.")
        has_digit = any(c.isdigit() for c in v)
        has_special = any(not c.isalnum() for c in v)
        if not (has_digit or has_special):
            raise ValueError("Senha deve conter ao menos um número ou caractere especial.")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Nome completo inválido.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ResendRequest(BaseModel):
    email: EmailStr


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_user_by_email(db: AsyncClient, email: str) -> dict | None:
    res = (
        await db.table("users")
        .select("*")
        .eq("email", email.lower())
        .maybe_single()
        .execute()
    )
    return res.data


async def _create_email_confirm_token(db: AsyncClient, user_id: str) -> str:
    raw_token = generate_email_token()
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_CONFIRM_TOKEN_EXPIRE_HOURS
    )
    await db.table("email_verification_tokens").insert({
        "user_id": user_id,
        "token_hash": token_hash,
        "expires_at": expires_at.isoformat(),
    }).execute()
    return raw_token


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncClient = Depends(get_db),
):
    """Cadastro de novo usuário. Rate-limit: 5/min por IP."""
    email = body.email.lower()

    existing = await _get_user_by_email(db, email)
    # Resposta genérica (200, não 201) para não vazar se o e-mail já existe
    if existing:
        return JSONResponse(
            status_code=200,
            content={"message": "Se este e-mail não estiver cadastrado, você receberá as instruções em breve."},
        )

    password_hash = hash_password(body.password)

    try:
        res = await db.table("users").insert({
            "email": email,
            "password_hash": password_hash,
            "full_name": body.full_name.strip(),
            "zip_code": body.zip_code.strip() or None,
        }).execute()
    except Exception as exc:
        logger.error("Erro ao criar usuário: %s", exc)
        raise HTTPException(status_code=500, detail="Erro interno. Tente novamente.")

    user = res.data[0]
    raw_token = await _create_email_confirm_token(db, user["id"])

    try:
        await send_confirmation_email(email, user["full_name"], raw_token)
    except Exception as exc:
        logger.error("Falha ao enviar e-mail de confirmação para %s: %s", email, exc)
        # Não falha o cadastro — usuário pode reenviar

    return {"message": "Cadastro realizado! Verifique seu e-mail para confirmar a conta."}


@router.get("/confirm-email/{token}")
async def confirm_email(token: str, db: AsyncClient = Depends(get_db)):
    """Confirma o e-mail do usuário via token."""
    token_hash = hash_token(token)
    now = datetime.now(timezone.utc)

    res = (
        await db.table("email_verification_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .is_("used_at", "null")
        .maybe_single()
        .execute()
    )
    record = res.data

    if not record:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado.")

    expires_at = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if now > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo link de confirmação.")

    # Marcar token como usado
    await db.table("email_verification_tokens").update({
        "used_at": now.isoformat(),
    }).eq("id", record["id"]).execute()

    # Confirmar e-mail do usuário
    await db.table("users").update({
        "email_confirmed": True,
        "email_confirmed_at": now.isoformat(),
    }).eq("id", record["user_id"]).execute()

    return {"message": "E-mail confirmado com sucesso! Agora você pode fazer login."}


@router.post("/login")
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncClient = Depends(get_db),
):
    """Login com e-mail e senha. Requer e-mail confirmado."""
    user = await _get_user_by_email(db, body.email)

    # Mensagem genérica para não vazar existência de conta (timing-safe check)
    generic_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha incorretos.",
    )

    if not user:
        dummy_verify()
        raise generic_error

    if not verify_password(body.password, user["password_hash"]):
        raise generic_error

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="E-mail não confirmado. Verifique sua caixa de entrada.",
        )

    if user.get("is_banned"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta suspensa.")

    # Gera tokens
    access_token = create_access_token(user["id"])
    raw_refresh = generate_refresh_token()
    refresh_hash = hash_token(raw_refresh)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")

    await db.table("refresh_tokens").insert({
        "user_id": user["id"],
        "token_hash": refresh_hash,
        "expires_at": expires_at.isoformat(),
        "ip_address": client_ip,
        "user_agent": user_agent[:255] if user_agent else None,
    }).execute()

    await db.table("users").update({
        "last_login_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", user["id"]).execute()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user": {
            "id": user["id"],
            "email": user["email"],
            "full_name": user["full_name"],
            "zip_code": user.get("zip_code"),
        },
    }


@router.post("/refresh")
async def refresh_token(body: RefreshRequest, db: AsyncClient = Depends(get_db)):
    """Renova o access token usando o refresh token."""
    token_hash = hash_token(body.refresh_token)
    now = datetime.now(timezone.utc)

    res = (
        await db.table("refresh_tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .is_("revoked_at", "null")
        .maybe_single()
        .execute()
    )
    record = res.data

    if not record:
        raise HTTPException(status_code=401, detail="Refresh token inválido.")

    expires_at = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if now > expires_at:
        raise HTTPException(status_code=401, detail="Refresh token expirado. Faça login novamente.")

    access_token = create_access_token(record["user_id"])
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/resend-confirmation")
@limiter.limit("3/hour")
async def resend_confirmation(
    request: Request,
    body: ResendRequest,
    db: AsyncClient = Depends(get_db),
):
    """Reenvia link de confirmação de e-mail."""
    user = await _get_user_by_email(db, body.email)

    # Resposta sempre genérica
    generic_ok = {"message": "Se sua conta existir e não estiver confirmada, você receberá um novo link em breve."}

    if not user or user["email_confirmed"]:
        return generic_ok

    raw_token = await _create_email_confirm_token(db, user["id"])
    try:
        await send_confirmation_email(user["email"], user["full_name"], raw_token)
    except Exception as exc:
        logger.error("Falha ao reenviar e-mail: %s", exc)

    return generic_ok


@router.post("/logout")
async def logout(
    user_id: str = Depends(get_current_user_id),
    body: RefreshRequest = None,  # type: ignore
    db: AsyncClient = Depends(get_db),
):
    """Revoga o refresh token atual."""
    if body and body.refresh_token:
        token_hash = hash_token(body.refresh_token)
        await db.table("refresh_tokens").update({
            "revoked_at": datetime.now(timezone.utc).isoformat(),
        }).eq("token_hash", token_hash).eq("user_id", user_id).execute()

    return {"message": "Logout realizado com sucesso."}
