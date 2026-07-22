from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.auth.service import (
    confirm_email,
    login_user,
    logout_user,
    refresh_session,
    register_user,
)
from app.database import get_db
from app.dependencies import get_current_user_id

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db=Depends(get_db),
):
    message = await register_user(db, body.email, body.password, body.full_name)
    return {"message": message}


@router.get("/confirm-email", response_model=MessageResponse)
async def confirm(
    token: str = Query(..., min_length=1),
    db=Depends(get_db),
):
    message = await confirm_email(db, token)
    return {"message": message}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    db=Depends(get_db),
):
    return await login_user(db, body.email, body.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db=Depends(get_db)):
    return await refresh_session(db, body.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: LogoutRequest,
    db=Depends(get_db),
    _: str = Depends(get_current_user_id),
):
    await logout_user(db, body.refresh_token)
    return {"message": "Logout realizado com sucesso"}
