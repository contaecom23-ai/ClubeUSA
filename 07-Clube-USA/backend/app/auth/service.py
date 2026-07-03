import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import asyncpg
import bcrypt
from jose import JWTError, jwt

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_jwt(user_id: str, email: str) -> tuple[str, int]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_hex(8),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(timedelta(days=settings.JWT_EXPIRE_DAYS).total_seconds())


def decode_jwt(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


async def register_user(
    pool: asyncpg.Pool,
    email: str,
    password: str,
    full_name: str,
    zip_code: Optional[str],
) -> dict:
    password_hash = hash_password(password)
    confirmation_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    async with pool.acquire() as conn:
        try:
            row = await conn.fetchrow(
                """
                INSERT INTO users (email, password_hash, full_name, zip_code,
                                   email_confirmation_token, email_confirmation_expires_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, email, full_name, zip_code, email_confirmed, created_at
                """,
                email.lower(),
                password_hash,
                full_name,
                zip_code,
                confirmation_token,
                expires_at,
            )
        except asyncpg.UniqueViolationError:
            return {"error": "email_taken"}

    return {"user": dict(row), "confirmation_token": confirmation_token}


async def confirm_email(pool: asyncpg.Pool, token: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE users
            SET email_confirmed = TRUE,
                email_confirmation_token = NULL,
                email_confirmation_expires_at = NULL,
                updated_at = NOW()
            WHERE email_confirmation_token = $1
              AND email_confirmation_expires_at > NOW()
              AND email_confirmed = FALSE
            RETURNING id, email, full_name, zip_code, email_confirmed, created_at
            """,
            token,
        )
    return dict(row) if row else None


async def authenticate_user(
    pool: asyncpg.Pool, email: str, password: str
) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, full_name, zip_code, password_hash, email_confirmed, created_at
            FROM users
            WHERE email = $1 AND is_active = TRUE
            """,
            email.lower(),
        )

    if not row:
        # Hash fictício para tempo constante — evita enumeração de usuários
        bcrypt.checkpw(b"dummy", b"$2b$12$KIXnKH.YKmXmxUCFtXZzFeQDZbOlW0ORkNbxEo3gWp18ZL5x6Wm1S")
        return None

    user = dict(row)
    if not verify_password(password, user["password_hash"]):
        return None

    return user


async def get_user_by_id(pool: asyncpg.Pool, user_id: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, email, full_name, zip_code, email_confirmed, created_at
            FROM users
            WHERE id = $1 AND is_active = TRUE
            """,
            uuid.UUID(user_id),
        )
    return dict(row) if row else None


async def reset_confirmation_token(
    pool: asyncpg.Pool, email: str
) -> Optional[str]:
    """Gera novo token de confirmação para reenvio de email."""
    new_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE users
            SET email_confirmation_token = $1,
                email_confirmation_expires_at = $2,
                updated_at = NOW()
            WHERE email = $3 AND email_confirmed = FALSE AND is_active = TRUE
            RETURNING full_name
            """,
            new_token,
            expires_at,
            email.lower(),
        )

    if not row:
        return None
    return new_token
