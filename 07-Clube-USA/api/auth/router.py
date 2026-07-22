from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from . import service
from .schemas import (
    ConfirmEmailRequest,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    user = await service.register_user(db, body.email, body.password, body.full_name)
    return RegisterResponse(
        message="Cadastro realizado! Verifique seu e-mail para confirmar a conta.",
        email=user.email,
    )


@router.get("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await service.confirm_email(db, token)
    return {"message": "E-mail confirmado com sucesso! Você já pode fazer login."}


@router.post("/resend-confirm", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def resend_confirm(
    request: Request,
    body: ForgotPasswordRequest,  # reutiliza {email} field
    db: AsyncSession = Depends(get_db),
) -> dict:
    await service.resend_confirm_email(db, body.email)
    return {"message": "Se o e-mail existir e não estiver confirmado, um novo link foi enviado."}


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    tokens = await service.login(db, body.email, body.password)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    tokens = await service.refresh_tokens(db, body.refresh_token)
    return TokenResponse(**tokens)


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await service.request_password_reset(db, body.email)
    return {"message": "Se o e-mail existir, um link de redefinição foi enviado."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    await service.reset_password(db, body.token, body.new_password)
    return {"message": "Senha redefinida com sucesso."}
