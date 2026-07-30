from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import (
    create_access_token,
    create_refresh_token,
    generate_email_confirm_token,
    hash_password,
    hash_refresh_token,
    verify_password_timing_safe,
)
from app.email.service import send_confirmation_email
from app.models import RefreshToken, User
from app.schemas import RegisterRequest


async def register_user(db: AsyncSession, data: RegisterRequest) -> User:
    result = await db.execute(select(User).where(User.email == data.email.lower()))
    if result.scalar_one_or_none():
        # Retorna o mesmo erro que "email não encontrado" para não vazar existência
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

    confirm_token, confirm_expires = generate_email_confirm_token()
    user = User(
        email=data.email.lower(),
        password_hash=hash_password(data.password),
        full_name=data.full_name.strip(),
        email_confirm_token=confirm_token,
        email_confirm_expires_at=confirm_expires,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await send_confirmation_email(user.email, user.full_name, confirm_token)
    return user


async def confirm_email(db: AsyncSession, token: str) -> None:
    result = await db.execute(
        select(User).where(User.email_confirm_token == token)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido ou expirado")
    now = datetime.now(timezone.utc)
    expires = user.email_confirm_expires_at
    # expires pode ser tz-aware ou naive; normaliza para tz-aware
    if expires and expires.tzinfo is None:
        from datetime import timezone as _tz
        expires = expires.replace(tzinfo=_tz.utc)
    if expires and expires < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")
    user.is_email_confirmed = True
    user.email_confirm_token = None
    user.email_confirm_expires_at = None
    await db.commit()


async def login_user(
    db: AsyncSession, email: str, password: str, user_agent: str = "", ip: str = ""
) -> tuple[str, str]:
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    # Sempre executa bcrypt (mesmo se usuário não existe) para prevenir timing attacks
    password_ok = verify_password_timing_safe(password, user.password_hash if user else None)
    if not user or not password_ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou senha incorretos")
    if not user.is_email_confirmed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada")

    access_token = create_access_token(str(user.id))
    raw_refresh, refresh_hash, refresh_expires = create_refresh_token()
    db.add(RefreshToken(
        user_id=user.id,
        token_hash=refresh_hash,
        expires_at=refresh_expires,
        user_agent=user_agent[:500] if user_agent else None,
        ip_address=ip[:45] if ip else None,
    ))
    await db.commit()
    return access_token, raw_refresh


async def refresh_tokens(db: AsyncSession, raw_refresh: str) -> tuple[str, str]:
    token_hash = hash_refresh_token(raw_refresh)
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > now,
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido ou expirado")

    result = await db.execute(select(User).where(User.id == rt.user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")

    # Rotaciona o refresh token (revoga o antigo, emite novo)
    rt.revoked_at = now
    raw_new, hash_new, expires_new = create_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=hash_new, expires_at=expires_new))
    access_token = create_access_token(str(user.id))
    await db.commit()
    return access_token, raw_new


async def logout_user(db: AsyncSession, raw_refresh: str) -> None:
    token_hash = hash_refresh_token(raw_refresh)
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    rt = result.scalar_one_or_none()
    if rt and rt.revoked_at is None:
        rt.revoked_at = datetime.now(timezone.utc)
        await db.commit()
