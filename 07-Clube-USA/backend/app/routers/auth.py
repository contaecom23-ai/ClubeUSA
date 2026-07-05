import logging
import secrets
from datetime import datetime, timedelta, timezone

import asyncpg
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.database import get_db
from app.limiter import limiter
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
    UpdateProfileRequest,
    UserProfile,
)
from app.services.email import send_confirmation_email
from app.utils.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


# ── Dependência: usuário autenticado ─────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: asyncpg.Connection = Depends(get_db),
) -> dict:
    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = await db.fetchrow(
        "SELECT id::text, email, full_name, zip_code, email_confirmed, created_at "
        "FROM users WHERE id = $1 AND is_active = TRUE",
        payload["sub"],
    )
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return dict(user)


# ── POST /auth/register ───────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    db: asyncpg.Connection = Depends(get_db),
):
    existing = await db.fetchval(
        "SELECT id FROM users WHERE email = $1", data.email.lower()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Este email já está cadastrado")

    confirm_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    try:
        user_id = await db.fetchval(
            """
            INSERT INTO users
                (email, password_hash, full_name, zip_code,
                 email_confirm_token, email_confirm_expires_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id::text
            """,
            data.email.lower(),
            hash_password(data.password),
            data.full_name.strip(),
            data.zip_code,
            confirm_token,
            expires_at,
        )
    except asyncpg.UniqueViolationError:
        raise HTTPException(status_code=409, detail="Este email já está cadastrado")

    try:
        await send_confirmation_email(data.email, data.full_name, confirm_token)
    except Exception:
        # Registro não falha se o email falhar — logamos para investigar
        logger.error("Falha ao enviar email de confirmação para %s***", data.email[:3])

    return {
        "message": "Cadastro realizado! Verifique seu email para confirmar a conta.",
        "user_id": user_id,
    }


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    db: asyncpg.Connection = Depends(get_db),
):
    settings = get_settings()
    user = await db.fetchrow(
        "SELECT id::text, email, password_hash, email_confirmed, is_active "
        "FROM users WHERE email = $1",
        data.email.lower(),
    )

    # Sempre verifica o hash para evitar timing attack
    dummy_hash = "$2b$12$invalidhashfortimingattackprevention0000000000000000000"
    password_ok = verify_password(
        data.password,
        user["password_hash"] if user else dummy_hash,
    )

    if not user or not password_ok or not user["is_active"]:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=403,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    token = create_access_token(user["id"], user["email"])
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRY_DAYS * 86400,
    )


# ── GET /auth/confirm/{token} ─────────────────────────────────────────────────

@router.get("/confirm/{token}")
async def confirm_email(
    token: str,
    db: asyncpg.Connection = Depends(get_db),
):
    settings = get_settings()
    user = await db.fetchrow(
        "SELECT id, email_confirm_expires_at FROM users "
        "WHERE email_confirm_token = $1 AND email_confirmed = FALSE",
        token,
    )

    if not user:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/login.html?confirm_error=invalid"
        )

    if user["email_confirm_expires_at"] < datetime.now(timezone.utc):
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/login.html?confirm_error=expired"
        )

    await db.execute(
        """
        UPDATE users
        SET email_confirmed = TRUE,
            email_confirm_token = NULL,
            email_confirm_expires_at = NULL
        WHERE id = $1
        """,
        user["id"],
    )

    return RedirectResponse(f"{settings.FRONTEND_URL}/login.html?confirmed=1")


# ── POST /auth/resend-confirmation ────────────────────────────────────────────

@router.post("/resend-confirmation", status_code=200)
@limiter.limit("3/minute")
async def resend_confirmation(
    request: Request,
    data: ResendConfirmationRequest,
    db: asyncpg.Connection = Depends(get_db),
):
    user = await db.fetchrow(
        "SELECT id, full_name, email_confirmed FROM users WHERE email = $1 AND is_active = TRUE",
        data.email.lower(),
    )

    # Resposta genérica para não revelar se o email existe
    if not user or user["email_confirmed"]:
        return {"message": "Se este email estiver cadastrado e não confirmado, você receberá um novo link."}

    confirm_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    await db.execute(
        "UPDATE users SET email_confirm_token = $1, email_confirm_expires_at = $2 WHERE id = $3",
        confirm_token,
        expires_at,
        user["id"],
    )

    try:
        await send_confirmation_email(data.email, user["full_name"], confirm_token)
    except Exception:
        logger.error("Falha ao reenviar email de confirmação para %s***", data.email[:3])

    return {"message": "Se este email estiver cadastrado e não confirmado, você receberá um novo link."}


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserProfile)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserProfile(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        zip_code=current_user.get("zip_code"),
        email_confirmed=current_user["email_confirmed"],
        created_at=current_user["created_at"].isoformat(),
    )


# ── PUT /auth/me ──────────────────────────────────────────────────────────────

@router.put("/me", response_model=UserProfile)
async def update_me(
    data: UpdateProfileRequest,
    current_user: dict = Depends(get_current_user),
    db: asyncpg.Connection = Depends(get_db),
):
    updates: dict = {}
    if data.full_name is not None:
        updates["full_name"] = data.full_name.strip()
    if data.zip_code is not None:
        updates["zip_code"] = data.zip_code

    if not updates:
        return UserProfile(
            id=current_user["id"],
            email=current_user["email"],
            full_name=current_user["full_name"],
            zip_code=current_user.get("zip_code"),
            email_confirmed=current_user["email_confirmed"],
            created_at=current_user["created_at"].isoformat(),
        )

    set_clauses = ", ".join(f"{k} = ${i + 2}" for i, k in enumerate(updates))
    values = list(updates.values())

    updated = await db.fetchrow(
        f"UPDATE users SET {set_clauses} WHERE id = $1 "
        "RETURNING id::text, email, full_name, zip_code, email_confirmed, created_at",
        current_user["id"],
        *values,
    )

    return UserProfile(
        id=updated["id"],
        email=updated["email"],
        full_name=updated["full_name"],
        zip_code=updated.get("zip_code"),
        email_confirmed=updated["email_confirmed"],
        created_at=updated["created_at"].isoformat(),
    )
