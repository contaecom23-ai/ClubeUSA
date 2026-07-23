import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr, field_validator

from .config import get_settings
from .db import get_conn
from .email_service import send_confirmation_email
from .jwt_utils import make_access_token
from .limiter import limiter
from .pw_utils import dummy_verify, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    referral_code: str | None = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome é obrigatório")
        if len(v) < 2:
            raise ValueError("Nome muito curto")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_token(user_id: str) -> str:
    s = get_settings()
    return make_access_token(user_id, s.SECRET_KEY, s.JWT_EXPIRE_DAYS)


def _safe_user(row: dict) -> dict:
    return {
        "id": str(row["id"]),
        "email": row["email"],
        "full_name": row["full_name"],
        "email_confirmed": row["email_confirmed"],
        "referral_code": row["referral_code"],
    }


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
@limiter.limit("5/minute")
async def register(body: RegisterRequest, request: Request, bg: BackgroundTasks):
    """Create a new account. Sends a confirmation email."""
    async with get_conn() as conn:
        # Resolve referrer — ignore silently if code is bad (never 422 on bad referral)
        referrer_id = None
        if body.referral_code:
            row = await conn.fetchrow(
                "SELECT id FROM users WHERE referral_code = $1", body.referral_code
            )
            if row:
                referrer_id = row["id"]

        # Same response for existing and new emails to prevent email enumeration
        existing = await conn.fetchval("SELECT 1 FROM users WHERE email = $1", body.email)
        if existing:
            return JSONResponse(
                status_code=200,
                content={"message": "Se este email ainda não estiver cadastrado, você receberá um link de confirmação."},
            )

        pw_hash = hash_password(body.password)
        confirm_token = secrets.token_urlsafe(32)
        confirm_expires = datetime.now(timezone.utc) + timedelta(hours=24)

        user = await conn.fetchrow(
            """
            INSERT INTO users
                (email, password_hash, full_name, email_confirm_token,
                 email_confirm_expires_at, referred_by_user_id)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, email, full_name, email_confirmed, referral_code
            """,
            body.email,
            pw_hash,
            body.full_name.strip(),
            confirm_token,
            confirm_expires,
            referrer_id,
        )

    # Fire-and-forget via FastAPI BackgroundTasks: email failure does not block registration
    bg.add_task(send_confirmation_email, body.email, body.full_name.strip(), confirm_token)

    return {
        "message": "Conta criada! Verifique seu email para confirmar o cadastro.",
        "user_id": str(user["id"]),
    }


@router.get("/confirm-email")
async def confirm_email(token: str):
    """Validate an email confirmation token and activate the account."""
    async with get_conn() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, full_name, email_confirmed, referral_code,
                   email_confirm_expires_at
            FROM users
            WHERE email_confirm_token = $1 AND is_active = TRUE
            """,
            token,
        )
        if not user:
            raise HTTPException(status_code=404, detail="Link inválido ou já utilizado")

        if user["email_confirmed"]:
            raise HTTPException(status_code=409, detail="Email já confirmado")

        expires = user["email_confirm_expires_at"]
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=410, detail="Link expirado — solicite um novo cadastro")

        await conn.execute(
            """
            UPDATE users
            SET email_confirmed = TRUE,
                email_confirm_token = NULL,
                email_confirm_expires_at = NULL
            WHERE id = $1
            """,
            user["id"],
        )

    # Build the user dict with the confirmed state (the row was fetched pre-update)
    confirmed_user = {**dict(user), "email_confirmed": True}
    access_token = _make_token(str(user["id"]))
    return TokenResponse(access_token=access_token, user=_safe_user(confirmed_user))


@router.post("/login")
@limiter.limit("10/minute")
async def login(body: LoginRequest, request: Request):
    """Exchange email + password for a JWT access token."""
    async with get_conn() as conn:
        user = await conn.fetchrow(
            """
            SELECT id, email, full_name, email_confirmed, referral_code, password_hash
            FROM users
            WHERE email = $1 AND is_active = TRUE
            """,
            body.email,
        )

    if not user:
        dummy_verify()  # Constant-time: don't reveal whether email exists
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=403,
            detail="Confirme seu email antes de fazer login. Verifique sua caixa de entrada.",
        )

    access_token = _make_token(str(user["id"]))
    return TokenResponse(access_token=access_token, user=_safe_user(dict(user)))
