from fastapi import APIRouter, Depends, Header, Query, Request

from ..database import get_db
from ..limiter import limiter
from .schemas import LoginRequest, MessageResponse, RefreshRequest, RegisterRequest, TokenResponse
from .service import (
    confirm_email,
    get_current_user_id,
    login_user,
    logout_user,
    refresh_access_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
async def register(request: Request, data: RegisterRequest, db=Depends(get_db)):
    await register_user(data, db)
    return MessageResponse(message="Cadastro realizado! Verifique seu email para ativar a conta.")


@router.get("/confirm-email", response_model=MessageResponse)
async def confirm(token: str = Query(..., min_length=1), db=Depends(get_db)):
    await confirm_email(token, db)
    return MessageResponse(message="Email confirmado com sucesso! Faça login para continuar.")


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db=Depends(get_db)):
    return await login_user(data, db)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, db=Depends(get_db)):
    return await refresh_access_token(data.refresh_token, db)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshRequest,
    authorization: str | None = Header(default=None),
    db=Depends(get_db),
):
    await get_current_user_id(authorization, db)
    await logout_user(data.refresh_token, db)
    return MessageResponse(message="Logout realizado.")
