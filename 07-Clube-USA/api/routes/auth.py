from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase import Client

from analytics import emit_event
from config import settings
from deps import get_db
from email_service import send_email_confirmation
from models import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
)
from security import (
    create_access_token,
    generate_referral_code,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

# Hash pré-computado para comparação em tempo constante quando usuário não existe (anti-timing)
_DUMMY_HASH = hash_password("clube-usa-dummy-timing-xf8k3n9-never-a-real-password")


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar novo usuário",
)
@limiter.limit(settings.REGISTER_RATE_LIMIT)
async def register(
    request: Request,
    body: RegisterRequest,
    db: Annotated[Client, Depends(get_db)],
) -> MessageResponse:
    # Anti-enumeração: mesma resposta independente de email já existir
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        return MessageResponse(
            message="Se este email for válido, você receberá um link de confirmação."
        )

    # Fase 0.2: resolve referral_code → referred_by_user_id (colunas já existem no schema)
    referred_by_user_id = None
    if body.referral_code:
        ref = (
            db.table("users")
            .select("id")
            .eq("referral_code", body.referral_code)
            .execute()
        )
        if ref.data:
            referred_by_user_id = ref.data[0]["id"]

    # Gera código de indicação único para o novo usuário
    referral_code = None
    for _ in range(10):
        candidate = generate_referral_code()
        if not db.table("users").select("id").eq("referral_code", candidate).execute().data:
            referral_code = candidate
            break

    confirm_token = generate_token()
    token_expires = datetime.now(timezone.utc) + timedelta(
        hours=settings.EMAIL_CONFIRM_TOKEN_TTL_HOURS
    )

    insert_result = db.table("users").insert(
        {
            "email": body.email,
            "password_hash": hash_password(body.password),
            "name": body.name,
            "phone": body.phone,
            "state": body.state,
            "city": body.city,
            "zip_code": body.zip_code,
            "referred_by_user_id": referred_by_user_id,
            "referral_code": referral_code,
            "email_confirm_token": confirm_token,
            "email_confirm_token_expires_at": token_expires.isoformat(),
        }
    ).execute()

    new_user_id = insert_result.data[0]["id"] if insert_result.data else None
    emit_event(db, "user_registered", user_id=new_user_id)
    if referred_by_user_id and new_user_id:
        emit_event(db, "referral_used", user_id=new_user_id,
                   metadata={"referrer_id": referred_by_user_id})

    send_email_confirmation(body.email, body.name, confirm_token)

    return MessageResponse(
        message="Cadastro realizado! Verifique seu email para confirmar sua conta."
    )


@router.get(
    "/confirm-email",
    response_model=MessageResponse,
    summary="Confirmar email via token do link",
)
async def confirm_email(
    token: str,
    db: Annotated[Client, Depends(get_db)],
) -> MessageResponse:
    now = datetime.now(timezone.utc)

    result = (
        db.table("users")
        .select("id, email_confirm_token_expires_at, email_confirmed_at")
        .eq("email_confirm_token", token)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=400, detail="Token inválido ou já utilizado")

    user = result.data[0]

    if user["email_confirmed_at"]:
        return MessageResponse(message="Email já confirmado. Faça login.")

    expires_at = datetime.fromisoformat(
        user["email_confirm_token_expires_at"].replace("Z", "+00:00")
    )
    if now > expires_at:
        raise HTTPException(
            status_code=400,
            detail="Token expirado. Solicite um novo email de confirmação.",
        )

    db.table("users").update(
        {
            "email_confirmed_at": now.isoformat(),
            "email_confirm_token": None,
            "email_confirm_token_expires_at": None,
        }
    ).eq("id", user["id"]).execute()

    emit_event(db, "email_confirmed", user_id=user["id"])

    return MessageResponse(message="Email confirmado com sucesso! Você já pode fazer login.")


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login com email e senha",
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login(
    request: Request,
    body: LoginRequest,
    db: Annotated[Client, Depends(get_db)],
) -> TokenResponse:
    result = (
        db.table("users")
        .select("id, password_hash, email_confirmed_at, is_active")
        .eq("email", body.email)
        .execute()
    )

    # Verifica hash mesmo se usuário não existe (tempo constante, anti-timing)
    candidate_hash = result.data[0]["password_hash"] if result.data else _DUMMY_HASH
    password_ok = verify_password(body.password, candidate_hash)

    if not result.data or not password_ok:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    user = result.data[0]

    if not user["is_active"]:
        raise HTTPException(
            status_code=403, detail="Conta desativada. Entre em contato com o suporte."
        )

    if not user["email_confirmed_at"]:
        raise HTTPException(
            status_code=403,
            detail="Email não confirmado. Verifique sua caixa de entrada ou solicite um novo link.",
        )

    access_token = create_access_token(user["id"])
    refresh_token = generate_token()
    refresh_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_TTL_DAYS
    )

    db.table("refresh_tokens").insert(
        {
            "user_id": user["id"],
            "token_hash": hash_token(refresh_token),
            "expires_at": refresh_expires.isoformat(),
        }
    ).execute()

    emit_event(db, "user_login", user_id=user["id"])

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renovar par de tokens via refresh token",
)
async def refresh(
    body: RefreshRequest,
    db: Annotated[Client, Depends(get_db)],
) -> TokenResponse:
    token_hash = hash_token(body.refresh_token)
    now = datetime.now(timezone.utc)

    result = (
        db.table("refresh_tokens")
        .select("id, user_id, expires_at, revoked_at")
        .eq("token_hash", token_hash)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    rt = result.data[0]

    if rt["revoked_at"]:
        raise HTTPException(status_code=401, detail="Refresh token revogado")

    expires_at = datetime.fromisoformat(rt["expires_at"].replace("Z", "+00:00"))
    if now > expires_at:
        raise HTTPException(status_code=401, detail="Refresh token expirado")

    # Rotação: revoga o token atual e emite novo par
    db.table("refresh_tokens").update({"revoked_at": now.isoformat()}).eq(
        "id", rt["id"]
    ).execute()

    user_result = (
        db.table("users").select("is_active").eq("id", rt["user_id"]).execute()
    )
    if not user_result.data or not user_result.data[0]["is_active"]:
        raise HTTPException(status_code=403, detail="Conta desativada")

    new_access = create_access_token(rt["user_id"])
    new_refresh = generate_token()
    new_expires = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_TTL_DAYS
    )

    db.table("refresh_tokens").insert(
        {
            "user_id": rt["user_id"],
            "token_hash": hash_token(new_refresh),
            "expires_at": new_expires.isoformat(),
        }
    ).execute()

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revogar refresh token (logout)",
)
async def logout(
    body: RefreshRequest,
    db: Annotated[Client, Depends(get_db)],
) -> MessageResponse:
    token_hash = hash_token(body.refresh_token)
    now = datetime.now(timezone.utc)
    db.table("refresh_tokens").update({"revoked_at": now.isoformat()}).eq(
        "token_hash", token_hash
    ).execute()
    return MessageResponse(message="Logout realizado com sucesso.")


@router.post(
    "/resend-confirmation",
    response_model=MessageResponse,
    summary="Reenviar email de confirmação",
)
@limiter.limit("3/minute")
async def resend_confirmation(
    request: Request,
    body: ResendConfirmationRequest,
    db: Annotated[Client, Depends(get_db)],
) -> MessageResponse:
    result = (
        db.table("users")
        .select("id, name, email_confirmed_at")
        .eq("email", body.email)
        .execute()
    )

    if result.data:
        user = result.data[0]
        if not user["email_confirmed_at"]:
            new_token = generate_token()
            expires = datetime.now(timezone.utc) + timedelta(
                hours=settings.EMAIL_CONFIRM_TOKEN_TTL_HOURS
            )
            db.table("users").update(
                {
                    "email_confirm_token": new_token,
                    "email_confirm_token_expires_at": expires.isoformat(),
                }
            ).eq("id", user["id"]).execute()
            send_email_confirmation(body.email, user["name"], new_token)

    # Anti-enumeração: sempre mesma resposta
    return MessageResponse(
        message="Se este email estiver cadastrado e não confirmado, você receberá um novo link."
    )
