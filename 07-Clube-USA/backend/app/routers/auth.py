from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status

from .. import database as db
from ..config import settings
from ..deps import current_user_id
from ..email_service import send_confirmation_email
from ..schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from ..security import (
    create_access_token,
    create_refresh_token,
    generate_email_token,
    generate_referral_code,
    hash_password,
    hash_refresh_token,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Registro ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request, bg: BackgroundTasks):
    # Verificar se email já existe
    existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", body.email.lower())
    if existing:
        # Retornar 409 sem revelar se o email existe (evita enumeração de usuários)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado.")

    # Resolver referred_by
    referred_by_id = None
    if body.referral_code:
        ref_user = await db.fetchrow(
            "SELECT id FROM users WHERE referral_code = $1", body.referral_code.upper()
        )
        if ref_user:
            referred_by_id = ref_user["id"]
        # Código inválido: ignoramos silenciosamente (não falhar o cadastro por isso)

    # Gerar referral_code único para o novo usuário
    for _ in range(5):  # até 5 tentativas em caso de colisão
        my_referral = generate_referral_code()
        clash = await db.fetchrow("SELECT id FROM users WHERE referral_code = $1", my_referral)
        if not clash:
            break
    else:
        my_referral = generate_referral_code() + "X"  # fallback improvável

    pw_hash = hash_password(body.password)

    user = await db.fetchrow(
        """
        INSERT INTO users (email, password_hash, full_name, phone, zip_code, city, state, referral_code, referred_by_user_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING id, full_name
        """,
        body.email.lower(),
        pw_hash,
        body.full_name,
        body.phone,
        body.zip_code,
        body.city,
        body.state,
        my_referral,
        referred_by_id,
    )

    # Criar token de confirmação (24h)
    email_token = generate_email_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.execute(
        "INSERT INTO email_confirmations (user_id, token, expires_at) VALUES ($1, $2, $3)",
        user["id"],
        email_token,
        expires,
    )

    bg.add_task(send_confirmation_email, body.email.lower(), user["full_name"], email_token)

    return {"message": "Cadastro realizado! Verifique seu email para confirmar a conta."}


# ── Confirmação de email ──────────────────────────────────────────────────────

@router.get("/confirm-email", response_model=MessageResponse)
async def confirm_email(token: str):
    now = datetime.now(timezone.utc)
    row = await db.fetchrow(
        """
        SELECT ec.id, ec.user_id, ec.expires_at, ec.used_at
        FROM email_confirmations ec
        WHERE ec.token = $1
        """,
        token,
    )

    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")
    if row["used_at"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token já utilizado.")
    if row["expires_at"] < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado.")

    # Marcar como usado e confirmar email do usuário (transação atômica)
    pool = db.get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE email_confirmations SET used_at = $1 WHERE id = $2",
                now,
                row["id"],
            )
            await conn.execute(
                "UPDATE users SET email_confirmed = TRUE, email_confirmed_at = $1 WHERE id = $2",
                now,
                row["user_id"],
            )

    return {"message": "Email confirmado com sucesso! Faça login para acessar sua conta."}


# ── Reenviar confirmação ──────────────────────────────────────────────────────

@router.post("/resend-confirmation", response_model=MessageResponse)
async def resend_confirmation(email_body: dict, bg: BackgroundTasks):
    # Aceita {"email": "..."} — sem autenticação (usuário não confirmou ainda)
    email = (email_body.get("email") or "").lower().strip()
    if not email:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email obrigatório.")

    user = await db.fetchrow(
        "SELECT id, full_name, email_confirmed FROM users WHERE email = $1 AND is_active = TRUE",
        email,
    )
    # Responder igual independente de o email existir (evitar enumeração)
    if not user or user["email_confirmed"]:
        return {"message": "Se o email existir e não estiver confirmado, um novo link será enviado."}

    # Invalidar tokens anteriores (marcar como usados)
    await db.execute(
        "UPDATE email_confirmations SET used_at = NOW() WHERE user_id = $1 AND used_at IS NULL",
        user["id"],
    )

    email_token = generate_email_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)
    await db.execute(
        "INSERT INTO email_confirmations (user_id, token, expires_at) VALUES ($1, $2, $3)",
        user["id"],
        email_token,
        expires,
    )
    bg.add_task(send_confirmation_email, email, user["full_name"], email_token)
    return {"message": "Se o email existir e não estiver confirmado, um novo link será enviado."}


# ── Login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    user = await db.fetchrow(
        "SELECT id, password_hash, email_confirmed, is_active FROM users WHERE email = $1",
        body.email.lower(),
    )

    # Credenciais inválidas → resposta genérica (não vazar qual campo está errado)
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos.",
        )
    if not user["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada.")
    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    user_id = str(user["id"])
    access_token = create_access_token(user_id)
    refresh_raw, refresh_hash = create_refresh_token()

    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
        user["id"],
        refresh_hash,
        expires_at,
    )
    await db.execute(
        "UPDATE users SET last_login_at = NOW() WHERE id = $1",
        user["id"],
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── Refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest):
    token_hash = hash_refresh_token(body.refresh_token)
    now = datetime.now(timezone.utc)

    row = await db.fetchrow(
        """
        SELECT id, user_id, expires_at, used_at, revoked_at
        FROM refresh_tokens
        WHERE token_hash = $1
        """,
        token_hash,
    )

    if not row or row["used_at"] or row["revoked_at"] or row["expires_at"] < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")

    # Rotação de refresh token (token anterior invalidado, novo emitido)
    user_id = str(row["user_id"])
    pool = db.get_pool()
    new_access = create_access_token(user_id)
    new_refresh_raw, new_refresh_hash = create_refresh_token()
    new_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE refresh_tokens SET used_at = $1 WHERE id = $2",
                now,
                row["id"],
            )
            await conn.execute(
                "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES ($1, $2, $3)",
                row["user_id"],
                new_refresh_hash,
                new_expires,
            )

    return TokenResponse(
        access_token=new_access,
        refresh_token=new_refresh_raw,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", response_model=MessageResponse)
async def logout(body: RefreshRequest, user_id: str = None):
    # Revogar o refresh token específico
    token_hash = hash_refresh_token(body.refresh_token)
    await db.execute(
        "UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = $1",
        token_hash,
    )
    return {"message": "Logout realizado."}


# ── Dev only: retorna token de confirmação (facilita testes sem email) ─────────

@router.get("/dev/pending-confirmation/{email}", include_in_schema=False)
async def dev_pending_confirmation(email: str):
    if not settings.DEBUG:
        raise HTTPException(status_code=404)
    row = await db.fetchrow(
        """
        SELECT ec.token, ec.expires_at
        FROM email_confirmations ec
        JOIN users u ON u.id = ec.user_id
        WHERE u.email = $1
          AND ec.used_at IS NULL
          AND ec.expires_at > NOW()
        ORDER BY ec.created_at DESC
        LIMIT 1
        """,
        email.lower(),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Nenhum token pendente.")
    return {"token": row["token"], "expires_at": row["expires_at"].isoformat()}
