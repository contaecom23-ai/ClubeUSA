import logging
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, EmailStr, field_validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..config import Settings, get_settings
from ..database import get_supabase
from ..services.auth_service import AuthService

logger = logging.getLogger(__name__)
router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


# ── Schemas ───────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    zip_code: str | None = None
    phone: str | None = None
    referral_code: str | None = None  # código de quem indicou

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Senha deve ter ao menos 8 caracteres")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome não pode ser vazio")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    email_confirmed: bool


class UserProfile(BaseModel):
    id: str
    email: str
    full_name: str
    zip_code: str | None
    phone: str | None
    email_confirmed: bool
    referral_code: str
    created_at: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    supabase=Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    """Cadastro de novo usuário. Envia email de confirmação."""
    svc = AuthService(supabase, settings)
    return await svc.register(data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    supabase=Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    """Login. Retorna JWT de acesso (7 dias)."""
    svc = AuthService(supabase, settings)
    return await svc.login(data.email, data.password)


@router.get("/confirm-email")
async def confirm_email(
    token: str,
    supabase=Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    """Confirma email via token enviado por email."""
    svc = AuthService(supabase, settings)
    return await svc.confirm_email(token)


@router.get("/me", response_model=UserProfile)
async def get_me(
    request: Request,
    supabase=Depends(get_supabase),
    settings: Settings = Depends(get_settings),
):
    """Retorna perfil do usuário autenticado. user_id vem do token (servidor)."""
    svc = AuthService(supabase, settings)
    user_id = svc.get_current_user_id(request)
    return await svc.get_profile(user_id)
