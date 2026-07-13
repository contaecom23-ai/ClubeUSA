import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from supabase import Client

from core.deps import get_current_user
from core.limiter import limiter
from core.supabase_client import get_supabase

from .schemas import (
    LoginRequest,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
    UserResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    supabase: Annotated[Client, Depends(get_supabase)],
):
    try:
        res = supabase.auth.admin.create_user(
            {
                "email": body.email,
                "password": body.password,
                "email_confirm": False,
                "user_metadata": {"full_name": body.full_name},
            }
        )
        user = res.user
    except Exception as e:
        msg = str(e).lower()
        if "already registered" in msg or "already exists" in msg or "duplicate" in msg:
            raise HTTPException(status_code=400, detail="Email já cadastrado")
        logger.error("register error: %s", e)
        raise HTTPException(status_code=500, detail="Falha no cadastro")

    try:
        supabase.table("profiles").insert(
            {"id": str(user.id), "full_name": body.full_name}
        ).execute()
    except Exception as e:
        # Profile creation failure is non-fatal; recoverable on first login
        logger.error("profile creation error for %s: %s", user.id, e)

    return {
        "message": "Cadastro realizado! Verifique seu email para confirmar a conta.",
        "user_id": str(user.id),
    }


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    supabase: Annotated[Client, Depends(get_supabase)],
):
    try:
        res = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
        session = res.session
        user = res.user
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ("invalid", "credentials", "not found", "email not confirmed")):
            raise HTTPException(status_code=401, detail="Email ou senha inválidos")
        logger.error("login error: %s", e)
        raise HTTPException(status_code=500, detail="Falha no login")

    if not session:
        raise HTTPException(status_code=401, detail="Autenticação falhou")

    return TokenResponse(
        access_token=session.access_token,
        user_id=str(user.id),
        email=user.email,
    )


@router.get("/me", response_model=UserResponse)
async def me(
    current_user: Annotated[dict, Depends(get_current_user)],
    supabase: Annotated[Client, Depends(get_supabase)],
):
    profile_res = (
        supabase.table("profiles")
        .select("full_name")
        .eq("id", current_user["id"])
        .maybe_single()
        .execute()
    )
    full_name = profile_res.data.get("full_name") if profile_res.data else None

    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        email_confirmed=bool(current_user.get("email_confirmed_at")),
        full_name=full_name,
    )


@router.post("/resend-confirmation")
@limiter.limit("3/minute")
async def resend_confirmation(
    request: Request,
    body: ResendConfirmationRequest,
    supabase: Annotated[Client, Depends(get_supabase)],
):
    try:
        supabase.auth.resend({"type": "signup", "email": body.email})
    except Exception as e:
        # Silently absorb errors to avoid email enumeration
        logger.warning("resend confirmation error (non-fatal): %s", e)

    return {"message": "Se o email estiver cadastrado, um link de confirmação foi enviado."}
