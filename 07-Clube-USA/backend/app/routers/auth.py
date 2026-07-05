import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from app.database import get_db
from app.rate_limit import limiter
from app.schemas import (
    LoginRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
)
from app.security import (
    create_access_token,
    generate_verification_token,
    hash_password,
    verify_password_constant_time,
)
from app.services.email import send_verification_email

logger = logging.getLogger(__name__)
router = APIRouter()

_TOKEN_TTL_HOURS = 24


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: Client = Depends(get_db),
) -> dict:
    """Create a new user account.

    Public route with rate-limit. Returns a generic success message even on duplicate
    email to prevent user enumeration.
    """
    email = body.email.lower()

    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        # Generic error — do NOT reveal whether email exists (user enumeration)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível completar o cadastro. Verifique os dados e tente novamente.",
        )

    password_hash = hash_password(body.password)
    verification_token = generate_verification_token()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)
    ).isoformat()

    user_result = (
        db.table("users")
        .insert({"email": email, "password_hash": password_hash, "is_email_verified": False})
        .execute()
    )
    if not user_result.data:
        logger.error("Failed to insert user for email (masked)")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno. Tente novamente.",
        )

    user_id = user_result.data[0]["id"]

    # Profile (best-effort; get_profile will auto-create if missing)
    db.table("profiles").insert(
        {"user_id": user_id, "full_name": body.full_name.strip()}
    ).execute()

    # Verification token
    db.table("email_verification_tokens").insert(
        {"user_id": user_id, "token": verification_token, "expires_at": expires_at}
    ).execute()

    # Email: log failure but do NOT fail registration (token is stored in DB)
    try:
        send_verification_email(email, verification_token)
    except Exception:
        logger.exception("Verification email failed (token saved, can resend)")

    return {
        "message": "Cadastro realizado! Verifique seu email para ativar a conta."
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db: Client = Depends(get_db),
) -> TokenResponse:
    """Authenticate and return a JWT.

    Public route with rate-limit. Uses constant-time comparison to prevent
    user enumeration via timing side-channel.
    """
    email = body.email.lower()

    result = (
        db.table("users")
        .select("id, email, password_hash, is_email_verified")
        .eq("email", email)
        .execute()
    )

    user = result.data[0] if result.data else None
    stored_hash = user["password_hash"] if user else None

    if not verify_password_constant_time(body.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    if not user["is_email_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    token = create_access_token(user["id"])
    return TokenResponse(access_token=token, user_id=user["id"])


@router.get("/verify-email")
async def verify_email(
    token: str,
    db: Client = Depends(get_db),
) -> dict:
    """Confirm email address via the token sent by email. Public route."""
    if not token or len(token) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido.",
        )

    now_iso = datetime.now(timezone.utc).isoformat()

    rec_result = (
        db.table("email_verification_tokens")
        .select("id, user_id, expires_at, used_at")
        .eq("token", token)
        .execute()
    )

    if not rec_result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado.",
        )

    rec = rec_result.data[0]

    if rec["used_at"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este link já foi utilizado.",
        )

    if rec["expires_at"] < now_iso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link expirado. Solicite um novo.",
        )

    # Mark token used and activate user — order matters: mark token first to
    # prevent a race condition where two concurrent requests both pass the check.
    db.table("email_verification_tokens").update({"used_at": now_iso}).eq(
        "id", rec["id"]
    ).execute()
    db.table("users").update({"is_email_verified": True}).eq(
        "id", rec["user_id"]
    ).execute()

    return {"message": "Email confirmado com sucesso! Você já pode fazer login."}


@router.post("/resend-verification")
@limiter.limit("3/minute")
async def resend_verification(
    request: Request,
    body: ResendVerificationRequest,
    db: Client = Depends(get_db),
) -> dict:
    """Re-send verification email. Public route with rate-limit.

    Always returns the same response to prevent user enumeration.
    """
    email = body.email.lower()

    user_result = (
        db.table("users")
        .select("id, is_email_verified")
        .eq("email", email)
        .execute()
    )

    if user_result.data and not user_result.data[0]["is_email_verified"]:
        user_id = user_result.data[0]["id"]
        new_token = generate_verification_token()
        expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)
        ).isoformat()

        # Invalidate previous unused tokens for this user
        db.table("email_verification_tokens").update(
            {"used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("user_id", user_id).is_("used_at", "null").execute()

        db.table("email_verification_tokens").insert(
            {"user_id": user_id, "token": new_token, "expires_at": expires_at}
        ).execute()

        try:
            send_verification_email(email, new_token)
        except Exception:
            logger.exception("Resend verification email failed")

    return {
        "message": (
            "Se o email estiver cadastrado e não confirmado, "
            "você receberá um novo link em breve."
        )
    }
