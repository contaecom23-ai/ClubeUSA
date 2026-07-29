import logging
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

import database
from auth import DUMMY_HASH, create_access_token, decode_token, hash_password, verify_password
from config import settings
from email_service import send_confirmation_email, send_welcome_email

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Clube USA API v0.1 starting")
    yield
    logger.info("Clube USA API shutting down")


app = FastAPI(
    title="Clube USA API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.debug else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

_origins = [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ──────────────────────────────── Schemas ────────────────────────────────────


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("A senha deve ter ao menos 8 caracteres.")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome completo é obrigatório.")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    zip_code: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: Optional[str]
    email_confirmed: bool
    created_at: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ──────────────────────────────── Helpers ────────────────────────────────────


def _user_out(row: dict) -> UserOut:
    return UserOut(
        id=row["id"],
        email=row["email"],
        full_name=row["full_name"],
        zip_code=row.get("zip_code"),
        email_confirmed=row["email_confirmed"],
        created_at=str(row["created_at"]),
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


# ──────────────────────────────── Routes ────────────────────────────────────


@app.get("/health", tags=["infra"])
def health():
    return {"status": "ok", "version": "0.1.0"}


# ─── Auth ────────────────────────────────────────────────────────────────────


@app.post("/auth/register", status_code=status.HTTP_201_CREATED, tags=["auth"])
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    db = database.get_db()

    existing = (
        db.table("users")
        .select("id")
        .eq("email", body.email.lower())
        .execute()
    )
    if existing.data:
        # Avoid user enumeration: same message regardless of why it failed.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível criar a conta com este email.",
        )

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    result = (
        db.table("users")
        .insert(
            {
                "email": body.email.lower(),
                "password_hash": hash_password(body.password),
                "full_name": body.full_name,
                "zip_code": body.zip_code,
                "email_confirmed": False,
                "email_confirmation_token": token,
                "email_confirmation_expires_at": expires_at,
            }
        )
        .execute()
    )
    if not result.data:
        logger.error("insert failed for email=%s", body.email)
        raise HTTPException(status_code=500, detail="Erro interno. Tente novamente.")

    send_confirmation_email(result.data[0]["email"], result.data[0]["full_name"], token)
    return {"message": "Conta criada! Verifique seu email para confirmar."}


@app.get("/auth/confirm-email", tags=["auth"])
@limiter.limit("10/minute")
async def confirm_email(request: Request, token: str):
    db = database.get_db()

    result = (
        db.table("users")
        .select("id, email, full_name, email_confirmed, email_confirmation_expires_at")
        .eq("email_confirmation_token", token)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=400, detail="Token inválido.")

    user = result.data[0]

    if user["email_confirmed"]:
        return {"message": "Email já confirmado."}

    expires_str = user["email_confirmation_expires_at"]
    expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        raise HTTPException(
            status_code=400,
            detail="Token expirado. Solicite um novo email de confirmação.",
        )

    db.table("users").update(
        {
            "email_confirmed": True,
            "email_confirmation_token": None,
            "email_confirmation_expires_at": None,
        }
    ).eq("id", user["id"]).execute()

    send_welcome_email(user["email"], user["full_name"])
    return {"message": "Email confirmado com sucesso! Bem-vindo ao Clube USA."}


@app.post("/auth/resend-confirmation", tags=["auth"])
@limiter.limit("3/minute")
async def resend_confirmation(request: Request, body: LoginRequest):
    """Requires email + password to avoid being abused as an email oracle."""
    db = database.get_db()

    result = (
        db.table("users")
        .select("id, email, full_name, password_hash, email_confirmed")
        .eq("email", body.email.lower())
        .execute()
    )
    # Use same error message as login to avoid user enumeration.
    if not result.data or not verify_password(body.password, result.data[0]["password_hash"]):
        raise HTTPException(status_code=400, detail="Credenciais inválidas.")

    user = result.data[0]
    if user["email_confirmed"]:
        return {"message": "Email já está confirmado."}

    new_token = secrets.token_urlsafe(32)
    new_expires = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    db.table("users").update(
        {
            "email_confirmation_token": new_token,
            "email_confirmation_expires_at": new_expires,
        }
    ).eq("id", user["id"]).execute()

    send_confirmation_email(user["email"], user["full_name"], new_token)
    return {"message": "Email de confirmação reenviado."}


@app.post("/auth/login", tags=["auth"])
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest):
    db = database.get_db()

    result = (
        db.table("users")
        .select("id, email, full_name, zip_code, password_hash, email_confirmed, created_at")
        .eq("email", body.email.lower())
        .execute()
    )
    # Always run bcrypt even when user not found to prevent timing-based enumeration.
    user = result.data[0] if result.data else None
    password_ok = verify_password(body.password, user["password_hash"] if user else DUMMY_HASH)

    if not user or not password_ok:
        raise HTTPException(status_code=401, detail="Email ou senha incorretos.")
    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=403,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    return TokenOut(
        access_token=create_access_token(user["id"], user["email"]),
        user=_user_out(user),
    )


# ─── Profile ─────────────────────────────────────────────────────────────────


@app.get("/profile/me", tags=["profile"])
async def get_profile(current_user: dict = Depends(get_current_user)):
    db = database.get_db()

    result = (
        db.table("users")
        .select("id, email, full_name, zip_code, email_confirmed, created_at")
        .eq("id", current_user["sub"])  # user_id from token, never from request
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _user_out(result.data[0])


@app.put("/profile/me", tags=["profile"])
async def update_profile(
    body: ProfileUpdateRequest,
    current_user: dict = Depends(get_current_user),
):
    update_data: dict = {}
    if body.full_name is not None:
        name = body.full_name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Nome não pode ser vazio.")
        update_data["full_name"] = name
    if body.zip_code is not None:
        update_data["zip_code"] = body.zip_code or None  # empty string → NULL

    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar.")

    db = database.get_db()
    result = (
        db.table("users")
        .update(update_data)
        .eq("id", current_user["sub"])  # user_id always from token
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return _user_out(result.data[0])
