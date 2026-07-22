"""Lógica de negócio para autenticação."""
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.email import build_confirm_email, build_password_reset_email, send_email
from core.security import (
    JWTError,
    create_access_token,
    create_refresh_token,
    decode_jwt,
    generate_opaque_token,
    hash_password,
    verify_password,
)
from models.user import User

logger = logging.getLogger(__name__)


async def register_user(db: AsyncSession, email: str, password: str, full_name: str | None) -> User:
    # 1. Checar e-mail duplicado — retorna 409 sem vazar se o usuário existe
    existing = await db.scalar(select(User).where(User.email == email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")

    # 2. Criar token de confirmação com TTL
    confirm_token = generate_opaque_token()
    confirm_expires = datetime.now(timezone.utc) + timedelta(
        seconds=settings.EMAIL_CONFIRM_TOKEN_TTL_SECONDS
    )

    user = User(
        email=email.lower(),
        hashed_password=hash_password(password),
        full_name=full_name,
        email_confirm_token=confirm_token,
        email_confirm_expires_at=confirm_expires,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # 3. Enviar e-mail de confirmação (não bloqueia o response se falhar)
    confirm_url = f"{settings.APP_URL}/auth/confirm-email?token={confirm_token}"
    try:
        await send_email(build_confirm_email(user.email, user.full_name or "", confirm_url))
    except Exception:
        logger.exception("Falha ao enviar e-mail de confirmação para %s", user.email)

    return user


async def confirm_email(db: AsyncSession, token: str) -> None:
    user = await db.scalar(select(User).where(User.email_confirm_token == token))

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    if user.email_confirmed:
        return  # idempotente

    now = datetime.now(timezone.utc)
    expires = user.email_confirm_expires_at
    if expires and expires.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado. Solicite um novo.")

    user.email_confirmed = True
    user.email_confirm_token = None
    user.email_confirm_expires_at = None
    await db.commit()


async def login(db: AsyncSession, email: str, password: str) -> dict:
    user = await db.scalar(select(User).where(User.email == email.lower()))

    # Resposta genérica (não vazar se e-mail existe)
    _invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="E-mail ou senha incorretos.",
    )

    if not user or not verify_password(password, user.hashed_password):
        raise _invalid

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada.")

    if not user.email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Confirme seu e-mail antes de fazer login.",
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    user_id = str(user.id)
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


async def refresh_tokens(db: AsyncSession, refresh_token: str) -> dict:
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido.")
    try:
        payload = decode_jwt(refresh_token)
        if payload.get("type") != "refresh":
            raise exc
        user_id: str = payload["sub"]
    except JWTError:
        raise exc

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise exc

    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


async def request_password_reset(db: AsyncSession, email: str) -> None:
    user = await db.scalar(select(User).where(User.email == email.lower()))
    # Não revelar se o e-mail existe — retorna 200 sempre
    if not user or not user.is_active:
        return

    token = generate_opaque_token()
    user.password_reset_token = token
    user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.PASSWORD_RESET_TOKEN_TTL_SECONDS
    )
    await db.commit()

    reset_url = f"{settings.APP_URL}/reset-password?token={token}"
    try:
        await send_email(build_password_reset_email(user.email, user.full_name or "", reset_url))
    except Exception:
        logger.exception("Falha ao enviar e-mail de reset para %s", user.email)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    user = await db.scalar(select(User).where(User.password_reset_token == token))

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    now = datetime.now(timezone.utc)
    expires = user.password_reset_expires_at
    if not expires or expires.replace(tzinfo=timezone.utc) < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado.")

    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires_at = None
    await db.commit()


async def resend_confirm_email(db: AsyncSession, email: str) -> None:
    user = await db.scalar(select(User).where(User.email == email.lower()))
    if not user or user.email_confirmed:
        return  # idempotente / não vaza

    token = generate_opaque_token()
    user.email_confirm_token = token
    user.email_confirm_expires_at = datetime.now(timezone.utc) + timedelta(
        seconds=settings.EMAIL_CONFIRM_TOKEN_TTL_SECONDS
    )
    await db.commit()

    confirm_url = f"{settings.APP_URL}/auth/confirm-email?token={token}"
    try:
        await send_email(build_confirm_email(user.email, user.full_name or "", confirm_url))
    except Exception:
        logger.exception("Falha ao reenviar e-mail de confirmação para %s", user.email)
