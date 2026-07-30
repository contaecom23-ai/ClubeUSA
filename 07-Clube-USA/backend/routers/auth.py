from fastapi import APIRouter, Depends, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from supabase import Client

from core.deps import get_current_user_id
from db.client import get_db
from schemas.auth import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
)
from services import auth_service

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest, db: Client = Depends(get_db)):
    result = auth_service.register_user(db, body.email, body.password, body.full_name)
    return MessageResponse(message=result["message"])


@router.post("/login", response_model=AuthResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: Client = Depends(get_db)):
    return auth_service.login_user(db, body.email, body.password)


@router.get("/confirm-email", response_model=MessageResponse)
async def confirm_email(token: str, db: Client = Depends(get_db)):
    result = auth_service.confirm_email(db, token)
    return MessageResponse(message=result["message"])


@router.post("/refresh", response_model=AuthResponse)
async def refresh(body: RefreshRequest, db: Client = Depends(get_db)):
    return auth_service.refresh_tokens(db, body.refresh_token)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    body: RefreshRequest,
    db: Client = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    result = auth_service.logout_user(db, user_id, body.refresh_token)
    return MessageResponse(message=result["message"])
