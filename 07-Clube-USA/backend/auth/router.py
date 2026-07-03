from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from auth.schemas import LoginRequest, MessageResponse, RefreshRequest, RegisterRequest, TokenResponse
from auth.service import login_user, refresh_access_token, register_user
from db.supabase import get_supabase
from supabase import Client

router = APIRouter(tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=MessageResponse)
@limiter.limit("5/minute")
async def register(
    request: Request,
    data: RegisterRequest,
    supabase: Client = Depends(get_supabase),
):
    return register_user(supabase, data)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    data: LoginRequest,
    supabase: Client = Depends(get_supabase),
):
    return login_user(supabase, data)


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    data: RefreshRequest,
    supabase: Client = Depends(get_supabase),
):
    return refresh_access_token(supabase, data.refresh_token)
