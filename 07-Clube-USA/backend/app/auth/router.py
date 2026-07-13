from fastapi import APIRouter, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.schemas import (
    ConfirmEmailRequest,
    LoginRequest,
    MessageResponse,
    RefreshTokenRequest,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
)
from app.auth.service import AuthError, confirm_email, login_user, refresh_access_token, register_user, resend_confirmation

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _auth_error_to_http(e: AuthError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.message)


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, body: RegisterRequest):
    try:
        result = register_user(body.email, body.password, body.full_name)
    except AuthError as e:
        raise _auth_error_to_http(e)

    msg = (
        "Cadastro realizado! Verifique seu email para confirmar a conta."
        if result["email_sent"]
        else "Cadastro realizado! Email de confirmacao nao enviado (SMTP nao configurado — contate o suporte)."
    )
    return {"message": msg}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: LoginRequest):
    try:
        result = login_user(body.email, body.password)
    except AuthError as e:
        raise _auth_error_to_http(e)
    return TokenResponse(**result, token_type="bearer")


@router.post("/confirm-email", response_model=MessageResponse)
def confirm(body: ConfirmEmailRequest):
    try:
        result = confirm_email(body.token)
    except AuthError as e:
        raise _auth_error_to_http(e)
    return result


@router.post("/resend-confirmation", response_model=MessageResponse)
@limiter.limit("3/minute")
def resend(request: Request, body: ResendConfirmationRequest):
    return resend_confirmation(body.email)


@router.post("/refresh", response_model=TokenResponse)
def refresh(body: RefreshTokenRequest):
    try:
        result = refresh_access_token(body.refresh_token)
    except AuthError as e:
        raise _auth_error_to_http(e)
    return TokenResponse(**result, token_type="bearer")
