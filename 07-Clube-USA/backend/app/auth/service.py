import logging
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import asyncpg
from fastapi import HTTPException, status

from ..config import get_settings
from .schemas import LoginRequest, RegisterRequest, TokenResponse
from .utils import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    generate_email_token,
    hash_password,
    verify_password,
)

# Hash dummy pré-computado para mitigação de timing attack no login.
# Gerado no módulo load para garantir formato compatível com o scheme atual.
_DUMMY_HASH = hash_password("dummy_senha_timing_mitigation")

log = logging.getLogger(__name__)


async def register_user(data: RegisterRequest, db: asyncpg.Connection) -> dict:
    existing = await db.fetchrow("SELECT id FROM users WHERE email = $1", data.email.lower())
    if existing:
        # Retorna 409 para email duplicado (não 400, para deixar claro que o email já existe)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email já cadastrado")

    pwd_hash = hash_password(data.password)
    confirm_token = generate_email_token()
    expires = datetime.now(timezone.utc) + timedelta(hours=24)

    row = await db.fetchrow(
        """
        INSERT INTO users
            (email, password_hash, name, estado, cidade, whatsapp,
             email_confirm_token, email_confirm_expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING id, email, name
        """,
        data.email.lower(),
        pwd_hash,
        data.name.strip(),
        data.estado,
        data.cidade.strip() if data.cidade else None,
        data.whatsapp,
        confirm_token,
        expires,
    )

    user = dict(row)
    await _send_confirmation_email(user["email"], user["name"], confirm_token)
    return user


async def confirm_email(token: str, db: asyncpg.Connection) -> None:
    row = await db.fetchrow(
        """
        SELECT id, email_confirm_expires_at
        FROM users
        WHERE email_confirm_token = $1
          AND email_confirmed = FALSE
          AND is_active = TRUE
        """,
        token,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token inválido ou já utilizado")

    if row["email_confirm_expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token expirado — solicite novo cadastro")

    await db.execute(
        """
        UPDATE users
        SET email_confirmed = TRUE,
            email_confirm_token = NULL,
            email_confirm_expires_at = NULL
        WHERE id = $1
        """,
        row["id"],
    )


async def login_user(data: LoginRequest, db: asyncpg.Connection) -> TokenResponse:
    row = await db.fetchrow(
        """
        SELECT id, password_hash, email_confirmed, is_active
        FROM users
        WHERE email = $1
        """,
        data.email.lower(),
    )

    # Verifica hash mesmo sem registro para evitar timing attack
    stored_hash = row["password_hash"] if row else _DUMMY_HASH

    if not verify_password(data.password, stored_hash) or not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="email ou senha incorretos",
        )

    if not row["is_active"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="conta desativada")

    if not row["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="confirme seu email antes de fazer login",
        )

    user_id = str(row["id"])
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token()

    s = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(days=s.refresh_token_expire_days)

    await db.execute(
        """
        INSERT INTO refresh_tokens (user_id, token, expires_at)
        VALUES ($1, $2, $3)
        """,
        row["id"],
        refresh_token,
        expires,
    )

    await db.execute(
        "UPDATE users SET last_login_at = NOW() WHERE id = $1",
        row["id"],
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


async def refresh_access_token(refresh_token: str, db: asyncpg.Connection) -> TokenResponse:
    row = await db.fetchrow(
        """
        SELECT rt.user_id, rt.expires_at, u.is_active, u.email_confirmed
        FROM refresh_tokens rt
        JOIN users u ON u.id = rt.user_id
        WHERE rt.token = $1 AND rt.revoked = FALSE
        """,
        refresh_token,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token inválido")

    if row["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh token expirado")

    if not row["is_active"] or not row["email_confirmed"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="acesso negado")

    # Rotaciona o refresh token (revoga o antigo, emite novo)
    new_refresh = create_refresh_token()
    s = get_settings()
    new_expires = datetime.now(timezone.utc) + timedelta(days=s.refresh_token_expire_days)

    async with db.transaction():
        await db.execute(
            "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
            refresh_token,
        )
        await db.execute(
            "INSERT INTO refresh_tokens (user_id, token, expires_at) VALUES ($1, $2, $3)",
            row["user_id"],
            new_refresh,
            new_expires,
        )

    return TokenResponse(
        access_token=create_access_token(str(row["user_id"])),
        refresh_token=new_refresh,
    )


async def logout_user(refresh_token: str, db: asyncpg.Connection) -> None:
    await db.execute(
        "UPDATE refresh_tokens SET revoked = TRUE WHERE token = $1",
        refresh_token,
    )


async def get_current_user_id(authorization: str | None, db: asyncpg.Connection) -> str:
    """Extrai e valida o user_id do Bearer token. Usado como dependency."""
    from jose import JWTError

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token ausente",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.removeprefix("Bearer ")
    try:
        user_id = decode_access_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    row = await db.fetchrow(
        "SELECT id FROM users WHERE id = $1 AND is_active = TRUE AND email_confirmed = TRUE",
        user_id,
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="usuário não encontrado")

    return str(row["id"])


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

async def _send_confirmation_email(email: str, name: str, token: str) -> None:
    s = get_settings()
    confirm_url = f"{s.frontend_url}/confirmar-email.html?token={token}"

    if not s.smtp_host:
        log.info("[DEV] Link de confirmação para %s: %s", email, confirm_url)
        return

    body_html = f"""
    <html><body>
    <h2>Olá, {name}!</h2>
    <p>Bem-vindo(a) ao <strong>Clube USA</strong>! Para ativar sua conta, clique no link abaixo:</p>
    <p><a href="{confirm_url}" style="
        background:#2563eb;color:#fff;padding:12px 24px;
        border-radius:6px;text-decoration:none;font-weight:bold;
    ">Confirmar meu email</a></p>
    <p>O link expira em <strong>24 horas</strong>.</p>
    <p style="color:#888;font-size:13px;">
        Se você não criou uma conta, ignore este email.
    </p>
    </body></html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"] = s.smtp_from
    msg["To"] = email
    msg.attach(MIMEText(body_html, "html"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.smtp_from, email, msg.as_string())
    except Exception:
        log.exception("Falha ao enviar email de confirmação para %s", email)
        # Não falha o cadastro se email não enviou — usuário pode re-enviar depois
