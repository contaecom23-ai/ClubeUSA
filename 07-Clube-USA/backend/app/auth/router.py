from fastapi import APIRouter, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.auth import schemas, service

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=schemas.MessageResponse, status_code=201)
@limiter.limit("5/minute")
def register(request: Request, body: schemas.RegisterRequest):
    """Cadastro de novo usuário. Rate-limit: 5 tentativas/min por IP."""
    return service.register_user(body)


@router.post("/login", response_model=schemas.TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, body: schemas.LoginRequest):
    """Login. Retorna access_token + refresh_token. Rate-limit: 10/min por IP."""
    return service.login_user(body)


@router.post("/refresh", response_model=schemas.TokenResponse)
def refresh(body: schemas.RefreshRequest):
    return service.refresh_token(body.refresh_token)


@router.post("/verify-email", response_model=schemas.MessageResponse)
def verify_email(body: schemas.VerifyEmailRequest):
    return service.verify_email(body.token_hash, body.type)


@router.post("/resend-verification", response_model=schemas.MessageResponse)
@limiter.limit("3/minute")
def resend_verification(request: Request, body: schemas.ResendVerificationRequest):
    return service.resend_verification(body.email)
