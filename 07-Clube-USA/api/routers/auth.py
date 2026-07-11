"""
Auth routes — the ONLY public endpoints are register, login, verify-email,
resend-confirmation, and refresh.
All others require a valid JWT (get_current_user_id dependency).

Security notes:
- user_id always from JWT, never from request body
- Login returns identical error for wrong email and wrong password (timing-safe)
- Rate limits: register 10/h, login 5/15min, resend 3/h
- Email confirmation token: UUID v4, 24h expiry
- Tokens are segregated by type claim: access tokens cannot be used at /refresh
  and refresh tokens are rejected at all other endpoints
"""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase import Client

from ..config import settings
from ..database import get_db
from ..models.user import (
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from ..services import email_service, password_service, token_service

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])

_GENERIC_AUTH_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email ou senha incorretos.",
)

# Pre-computed bcrypt hash used for timing-safe login when email not found.
# Value is irrelevant (password unknown); purpose is equal compute time.
_DUMMY_HASH = "$2b$12$eImiTXuWVxfM37uY4JANjQ.o6OcOE7WcUqgthQ6jTODkB7hGf3oTK"


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    body: RegisterRequest,
    db: Client = Depends(get_db),
) -> MessageResponse:
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está cadastrado.",
        )

    confirm_token = str(uuid.uuid4())
    confirm_expires = datetime.now(timezone.utc) + timedelta(hours=24)

    new_user = {
        "email": body.email,
        "password_hash": password_service.hash_password(body.password),
        "full_name": body.full_name,
        "email_confirmed": False,
        "email_confirm_token": confirm_token,
        "email_confirm_expires_at": confirm_expires.isoformat(),
    }
    result = db.table("users").insert(new_user).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar conta.")

    confirm_url = f"{settings.FRONTEND_URL}/verify-email.html?token={confirm_token}"
    email_service.send_confirmation_email(body.email, confirm_url)

    return MessageResponse(
        message="Conta criada! Verifique seu email para ativar sua conta."
    )


@router.post("/verify-email", response_model=TokenResponse)
async def verify_email(
    body: VerifyEmailRequest,
    db: Client = Depends(get_db),
) -> TokenResponse:
    now = datetime.now(timezone.utc)

    result = (
        db.table("users")
        .select("id, email, full_name, email_confirmed, email_confirm_expires_at")
        .eq("email_confirm_token", body.token)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")

    user = result.data[0]

    if user["email_confirmed"]:
        raise HTTPException(status_code=400, detail="Email já confirmado. Faça login.")

    expires_at = datetime.fromisoformat(user["email_confirm_expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise HTTPException(
            status_code=400,
            detail="Link de confirmação expirado. Solicite um novo.",
        )

    db.table("users").update(
        {
            "email_confirmed": True,
            "email_confirm_token": None,
            "email_confirm_expires_at": None,
            "updated_at": now.isoformat(),
        }
    ).eq("id", user["id"]).execute()

    email_service.send_welcome_email(user["email"], user["full_name"])

    return TokenResponse(
        access_token=token_service.create_access_token(user["id"]),
        refresh_token=token_service.create_refresh_token(user["id"]),
        expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    body: LoginRequest,
    db: Client = Depends(get_db),
) -> TokenResponse:
    result = (
        db.table("users")
        .select("id, password_hash, email_confirmed")
        .eq("email", body.email)
        .execute()
    )

    stored_hash = result.data[0]["password_hash"] if result.data else _DUMMY_HASH
    password_ok = password_service.verify_password(body.password, stored_hash)

    if not result.data or not password_ok:
        raise _GENERIC_AUTH_ERROR

    user = result.data[0]
    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    return TokenResponse(
        access_token=token_service.create_access_token(user["id"]),
        refresh_token=token_service.create_refresh_token(user["id"]),
        expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(body: RefreshTokenRequest) -> TokenResponse:
    """Issue a new access token from a valid refresh token.

    The refresh token is NOT rotated — the same refresh token works until it
    expires (7 days). Token rotation can be added later when a revocation store
    (DB table) is available.
    """
    user_id = token_service.decode_refresh_token(body.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado. Faça login novamente.",
        )
    return TokenResponse(
        access_token=token_service.create_access_token(user_id),
        refresh_token=body.refresh_token,  # return the same refresh token
        expires_in_days=settings.ACCESS_TOKEN_EXPIRE_DAYS,
    )


@router.post("/resend-confirmation", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_RESEND)
async def resend_confirmation(
    request: Request,
    body: ResendConfirmationRequest,
    db: Client = Depends(get_db),
) -> MessageResponse:
    result = (
        db.table("users")
        .select("id, email, full_name, email_confirmed")
        .eq("email", body.email)
        .execute()
    )

    if result.data and not result.data[0]["email_confirmed"]:
        user = result.data[0]
        new_token = str(uuid.uuid4())
        new_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        db.table("users").update(
            {
                "email_confirm_token": new_token,
                "email_confirm_expires_at": new_expires.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("id", user["id"]).execute()

        confirm_url = f"{settings.FRONTEND_URL}/verify-email.html?token={new_token}"
        email_service.send_confirmation_email(user["email"], confirm_url)

    return MessageResponse(
        message="Se esse email estiver cadastrado e não confirmado, você receberá um novo link."
    )
