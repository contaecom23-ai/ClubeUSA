from fastapi import APIRouter, Depends, HTTPException, Request
from gotrue.errors import AuthApiError
from supabase import Client

from app.config import Settings, get_settings
from app.dependencies import get_current_user, get_supabase
from app.limiter import limiter
from app.schemas.auth import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _supabase_error_to_http(e: AuthApiError) -> HTTPException:
    msg = str(e).lower()
    if "already registered" in msg or "already exists" in msg:
        return HTTPException(400, "Este email já está cadastrado")
    if "email not confirmed" in msg:
        return HTTPException(403, "Email não confirmado. Verifique sua caixa de entrada.")
    if "invalid login credentials" in msg or "invalid credentials" in msg:
        return HTTPException(401, "Email ou senha incorretos")
    if "too many requests" in msg or "rate limit" in msg:
        return HTTPException(429, "Muitas tentativas. Aguarde alguns minutos.")
    if "weak password" in msg or "password" in msg:
        return HTTPException(400, "Senha não atende aos requisitos mínimos")
    return HTTPException(400, "Erro ao processar solicitação. Tente novamente.")


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    body: RegisterRequest,
    supabase: Client = Depends(get_supabase),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    try:
        supabase.auth.sign_up(
            {
                "email": body.email,
                "password": body.password,
                "options": {
                    "data": {
                        "first_name": body.first_name,
                        "last_name": body.last_name,
                        "zip_code": body.zip_code,
                        "phone": body.phone,
                    }
                },
            }
        )
    except AuthApiError as e:
        raise _supabase_error_to_http(e)

    return MessageResponse(
        message="Cadastro realizado! Verifique seu email para confirmar a conta."
    )


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: LoginRequest,
    supabase: Client = Depends(get_supabase),
) -> TokenResponse:
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": body.email, "password": body.password}
        )
    except AuthApiError as e:
        raise _supabase_error_to_http(e)

    if not response.session:
        raise HTTPException(403, "Email não confirmado. Verifique sua caixa de entrada.")

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 3600,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    body: RefreshRequest,
    supabase: Client = Depends(get_supabase),
) -> TokenResponse:
    try:
        response = supabase.auth.refresh_session(body.refresh_token)
    except AuthApiError as e:
        raise _supabase_error_to_http(e)

    if not response.session:
        raise HTTPException(401, "Sessão inválida ou expirada")

    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        expires_in=response.session.expires_in or 3600,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase),
) -> MessageResponse:
    try:
        supabase.auth.sign_out()
    except AuthApiError:
        pass

    return MessageResponse(message="Logout realizado com sucesso")
