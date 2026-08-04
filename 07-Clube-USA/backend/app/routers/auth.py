from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import settings
from ..database import get_db
from ..dependencies import get_current_user
from ..models.user import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from ..services.auth_service import (
    create_access_token,
    generate_confirmation_token,
    generate_referral_code,
    hash_password,
    verify_password,
)
from ..services.email_service import send_confirmation_email

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# Dummy hash para timing-safe login (evita enumeração de emails via timing)
_DUMMY_HASH = "$2b$12$GfQ1B2AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def _to_user_response(u: dict) -> UserResponse:
    return UserResponse(
        id=u["id"],
        email=u["email"],
        full_name=u["full_name"],
        zip_code=u.get("zip_code"),
        referral_code=u["referral_code"],
        email_confirmed=bool(u.get("email_confirmed_at")),
        created_at=u["created_at"],
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(request: Request, body: RegisterRequest):
    db = get_db()

    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email já cadastrado. Tente fazer login.",
        )

    referral_code = generate_referral_code()
    while db.table("users").select("id").eq("referral_code", referral_code).execute().data:
        referral_code = generate_referral_code()

    result = db.table("users").insert({
        "email": body.email,
        "password_hash": hash_password(body.password),
        "full_name": body.full_name,
        "zip_code": body.zip_code,
        "referral_code": referral_code,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar conta")

    user = result.data[0]
    token = generate_confirmation_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_CONFIRMATION_EXPIRE_HOURS)

    db.table("email_confirmations").insert({
        "user_id": user["id"],
        "token": token,
        "expires_at": expires.isoformat(),
    }).execute()

    send_confirmation_email(body.email, body.full_name, token)

    return {
        "message": "Conta criada! Verifique seu email para confirmar o cadastro.",
        "email": body.email,
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(request: Request, body: LoginRequest):
    db = get_db()
    result = db.table("users").select("*").eq("email", body.email).execute()
    user = result.data[0] if result.data else None

    # Sempre rodar verify_password para evitar timing attack
    password_ok = verify_password(body.password, user["password_hash"] if user else _DUMMY_HASH)

    if not user or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")

    return TokenResponse(
        access_token=create_access_token(user["id"]),
        user=_to_user_response(user),
    )


@router.post("/verify-email")
async def verify_email(token: str):
    db = get_db()
    now = datetime.now(timezone.utc)

    conf = db.table("email_confirmations").select("*").eq("token", token).execute()
    record = conf.data[0] if conf.data else None

    if not record:
        raise HTTPException(status_code=404, detail="Token inválido")
    if record.get("used_at"):
        raise HTTPException(status_code=400, detail="Token já utilizado")

    expires_at = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if now > expires_at:
        raise HTTPException(status_code=400, detail="Token expirado. Solicite um novo link.")

    db.table("email_confirmations").update({"used_at": now.isoformat()}).eq("id", record["id"]).execute()
    db.table("users").update({"email_confirmed_at": now.isoformat()}).eq("id", record["user_id"]).execute()

    return {"message": "Email confirmado com sucesso! Faça login para continuar."}


@router.post("/resend-confirmation")
@limiter.limit(settings.RATE_LIMIT_RESEND)
async def resend_confirmation(request: Request, email: str):
    db = get_db()
    result = db.table("users").select("*").eq("email", email).execute()
    user = result.data[0] if result.data else None

    # Resposta genérica: não revelar se email existe
    generic_ok = {"message": "Se o email existir, você receberá um novo link em breve."}

    if not user:
        return generic_ok
    if user.get("email_confirmed_at"):
        return {"message": "Email já confirmado. Faça login normalmente."}

    # Invalidar tokens pendentes
    db.table("email_confirmations").update({"used_at": datetime.now(timezone.utc).isoformat()}) \
        .eq("user_id", user["id"]).is_("used_at", "null").execute()

    token = generate_confirmation_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_CONFIRMATION_EXPIRE_HOURS)
    db.table("email_confirmations").insert({
        "user_id": user["id"],
        "token": token,
        "expires_at": expires.isoformat(),
    }).execute()

    send_confirmation_email(email, user["full_name"], token)
    return generic_ok
