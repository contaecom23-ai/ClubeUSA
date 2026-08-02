from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..database import get_db
from ..email_service import send_confirmation_email
from ..models import LoginRequest, MessageResponse, RegisterRequest, TokenResponse
from ..security import (
    create_access_token,
    generate_email_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

EMAIL_TOKEN_TTL_HOURS = 24


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest) -> MessageResponse:
    db = get_db()
    email = body.email.lower().strip()

    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        # Resposta genérica — não confirmar se email existe (anti-enumeration)
        return MessageResponse(message="Se este email for novo, você receberá um link de confirmação.")

    confirm_token = generate_email_token()
    confirm_sent_at = datetime.now(tz=timezone.utc).isoformat()

    result = db.table("users").insert({
        "email": email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name.strip(),
        "email_confirmed": False,
        "email_confirm_token": confirm_token,
        "email_confirm_sent_at": confirm_sent_at,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar conta")

    user_id = result.data[0]["id"]

    # Cria perfil vazio vinculado ao user
    db.table("profiles").insert({"user_id": user_id}).execute()

    try:
        send_confirmation_email(email, body.full_name.strip(), confirm_token)
    except Exception:
        logger.exception("Falha ao enviar email de confirmação para %s", email)
        # Não falha o cadastro — o usuário pode solicitar reenvio

    return MessageResponse(message="Conta criada! Verifique seu email para confirmar o cadastro.")


@router.get("/confirm-email", response_model=MessageResponse)
async def confirm_email(token: str) -> MessageResponse:
    if not token or len(token) > 128:
        raise HTTPException(status_code=400, detail="Token inválido")

    db = get_db()
    result = db.table("users").select("id,email_confirm_sent_at,email_confirmed").eq(
        "email_confirm_token", token
    ).execute()

    if not result.data:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")

    user = result.data[0]

    if user["email_confirmed"]:
        return MessageResponse(message="Email já confirmado. Faça login.")

    sent_at = datetime.fromisoformat(user["email_confirm_sent_at"])
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    if datetime.now(tz=timezone.utc) - sent_at > timedelta(hours=EMAIL_TOKEN_TTL_HOURS):
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo link.")

    db.table("users").update({
        "email_confirmed": True,
        "email_confirm_token": None,
        "email_confirm_sent_at": None,
    }).eq("id", user["id"]).execute()

    return MessageResponse(message="Email confirmado com sucesso! Agora você pode fazer login.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest) -> TokenResponse:
    db = get_db()
    email = body.email.lower().strip()

    result = db.table("users").select(
        "id,password_hash,email_confirmed"
    ).eq("email", email).execute()

    # Timing constante para evitar user enumeration
    if not result.data:
        verify_password("dummy", "$2b$12$" + "x" * 53)
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    user = result.data[0]
    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    token, expires_at = create_access_token(user["id"])
    return TokenResponse(
        access_token=token,
        expires_at=expires_at,
        email_confirmed=user["email_confirmed"],
    )


@router.post("/resend-confirmation", response_model=MessageResponse)
@limiter.limit("3/minute")
async def resend_confirmation(request: Request, body: LoginRequest) -> MessageResponse:
    """Requer email + senha para não virar vetor de spam."""
    db = get_db()
    email = body.email.lower().strip()

    result = db.table("users").select(
        "id,full_name,password_hash,email_confirmed"
    ).eq("email", email).execute()

    # Resposta genérica sempre
    generic = MessageResponse(message="Se o email existir e não estiver confirmado, você receberá um novo link.")

    if not result.data:
        verify_password("dummy", "$2b$12$" + "x" * 53)
        return generic

    user = result.data[0]
    if not verify_password(body.password, user["password_hash"]):
        return generic

    if user["email_confirmed"]:
        return generic

    new_token = generate_email_token()
    db.table("users").update({
        "email_confirm_token": new_token,
        "email_confirm_sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }).eq("id", user["id"]).execute()

    try:
        send_confirmation_email(email, user["full_name"], new_token)
    except Exception:
        logger.exception("Falha ao reenviar email")

    return generic
