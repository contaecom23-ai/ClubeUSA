from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.auth.service import AuthError, confirm_email, login_user, refresh_tokens, register_user
from app.database import get_db

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/hour")
def register(request: Request, body: RegisterRequest):
    db = get_db()
    try:
        register_user(
            db,
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            phone=body.phone,
            zip_code=body.zip_code,
        )
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return {"message": "Conta criada. Verifique seu email para confirmar o cadastro."}


@router.get("/confirm-email", response_model=MessageResponse)
def confirm(token: str):
    db = get_db()
    ok = confirm_email(db, token)
    if not ok:
        raise HTTPException(status_code=400, detail="Token inválido ou expirado.")
    return {"message": "Email confirmado com sucesso. Você já pode fazer login."}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/15minutes")
def login(request: Request, body: LoginRequest):
    db = get_db()
    try:
        access_token, refresh_token = login_user(db, body.email, body.password)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshRequest):
    db = get_db()
    try:
        access_token, new_refresh = refresh_tokens(db, body.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    return TokenResponse(access_token=access_token, refresh_token=new_refresh)
