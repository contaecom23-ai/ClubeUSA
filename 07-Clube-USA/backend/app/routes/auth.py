from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from asyncpg import Connection
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_conn
from app.models.user import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
    ConfirmEmailRequest,
    MessageResponse,
)
from app.utils.security import (
    hash_password,
    verify_password,
    generate_token,
    hash_token,
    create_access_token,
)
from app.utils.email import send_confirmation_email
from app.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Limiter compartilhado com app.state.limiter (registrado em main.py)
_limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# POST /api/auth/register  — 5 cadastros/hora por IP (anti spam)
# ---------------------------------------------------------------------------
@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
@_limiter.limit("5/hour")
async def register(request: Request, body: RegisterRequest, conn: Connection = Depends(get_conn)):
    existing = await conn.fetchrow("SELECT id FROM users WHERE email = $1", body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe uma conta com este email.",
        )

    password_hash = hash_password(body.password)
    confirmation_token = generate_token(32)
    confirmation_token_hash = hash_token(confirmation_token)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.EMAIL_TOKEN_EXPIRE_HOURS)

    await conn.execute(
        """
        INSERT INTO users (email, password_hash, full_name, zip_code,
                           email_confirmation_token, email_confirmation_expires_at)
        VALUES ($1, $2, $3, $4, $5, $6)
        """,
        body.email,
        password_hash,
        body.full_name,
        body.zip_code,
        confirmation_token_hash,
        expires_at,
    )

    send_confirmation_email(body.email, body.full_name, confirmation_token)

    return MessageResponse(
        message=(
            "Cadastro realizado! Verifique seu email para confirmar a conta. "
            "O link expira em 24 horas."
        )
    )


# ---------------------------------------------------------------------------
# POST /api/auth/confirm-email
# ---------------------------------------------------------------------------
@router.post("/confirm-email", response_model=MessageResponse)
async def confirm_email(body: ConfirmEmailRequest, conn: Connection = Depends(get_conn)):
    token_hash = hash_token(body.token)
    row = await conn.fetchrow(
        """
        SELECT id, email_confirmed, email_confirmation_expires_at
        FROM users
        WHERE email_confirmation_token = $1
        """,
        token_hash,
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou já utilizado.",
        )

    if row["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já confirmado.",
        )

    expires_at = row["email_confirmation_expires_at"]
    if expires_at and expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Faça login para solicitar um novo link de confirmação.",
        )

    await conn.execute(
        """
        UPDATE users
        SET email_confirmed = TRUE,
            email_confirmation_token = NULL,
            email_confirmation_expires_at = NULL
        WHERE id = $1
        """,
        row["id"],
    )

    return MessageResponse(message="Email confirmado com sucesso! Você já pode fazer login.")


# ---------------------------------------------------------------------------
# POST /api/auth/login  — 10 tentativas/minuto por IP (anti brute-force)
# ---------------------------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
@_limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, conn: Connection = Depends(get_conn)):
    row = await conn.fetchrow(
        "SELECT id, password_hash, email_confirmed, is_active FROM users WHERE email = $1",
        body.email,
    )

    # Timing constante: verifica senha mesmo sem match para evitar user enumeration via tempo de resposta
    _DUMMY_HASH = "$2b$12$PihKa0EuAZSDDK38Gw0uUurnEPFLRNrBHkmMEJc3pOIpmRRBnDtFu"
    stored_hash = row["password_hash"] if row else _DUMMY_HASH

    if not verify_password(body.password, stored_hash) or not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
        )

    if not row["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com o suporte.",
        )

    if not row["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    user_id = str(row["id"])
    access_token, _ = create_access_token(user_id)

    raw_refresh = generate_token(48)
    refresh_hash = hash_token(raw_refresh)
    refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    user_agent = request.headers.get("user-agent", "")[:256]
    ip_address = request.client.host if request.client else ""

    await conn.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
        VALUES ($1, $2, $3, $4, $5)
        """,
        row["id"],
        refresh_hash,
        refresh_expires,
        user_agent,
        ip_address,
    )

    await conn.execute(
        "UPDATE users SET last_login_at = NOW() WHERE id = $1",
        row["id"],
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


# ---------------------------------------------------------------------------
# POST /api/auth/refresh
# ---------------------------------------------------------------------------
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, request: Request, conn: Connection = Depends(get_conn)):
    token_hash = hash_token(body.refresh_token)
    row = await conn.fetchrow(
        """
        SELECT rt.id, rt.user_id, rt.expires_at, rt.revoked_at, u.is_active
        FROM refresh_tokens rt
        JOIN users u ON u.id = rt.user_id
        WHERE rt.token_hash = $1
        """,
        token_hash,
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")
    if row["revoked_at"] is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revogado.")
    if row["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado.")
    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada.")

    # Rotação: revoga o antigo, emite novo
    await conn.execute(
        "UPDATE refresh_tokens SET revoked_at = NOW() WHERE id = $1",
        row["id"],
    )

    user_id = str(row["user_id"])
    access_token, _ = create_access_token(user_id)

    new_raw_refresh = generate_token(48)
    new_refresh_hash = hash_token(new_raw_refresh)
    new_refresh_expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    user_agent = request.headers.get("user-agent", "")[:256]
    ip_address = request.client.host if request.client else ""

    await conn.execute(
        """
        INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
        VALUES ($1, $2, $3, $4, $5)
        """,
        row["user_id"],
        new_refresh_hash,
        new_refresh_expires,
        user_agent,
        ip_address,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400,
    )


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------
@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshRequest, conn: Connection = Depends(get_conn)):
    token_hash = hash_token(body.refresh_token)
    await conn.execute(
        "UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = $1 AND revoked_at IS NULL",
        token_hash,
    )
    # Sempre 200: idempotente e não vaza info sobre existência do token
    return MessageResponse(message="Logout realizado com sucesso.")
