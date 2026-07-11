from fastapi import APIRouter, Depends, Request, status
from supabase import Client

from app.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResendVerificationRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from app.auth.service import (
    login_user,
    refresh_access_token,
    register_user,
    resend_verification,
    verify_email,
)
from app.config import get_settings
from app.database import get_db
from app.rate_limit import check_rate_limit

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=MessageResponse)
async def register(req: RegisterRequest, request: Request, db: Client = Depends(get_db)):
    s = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        db,
        key=f"register:{client_ip}",
        action="register",
        max_attempts=s.rate_limit_register_max,
        window_seconds=s.rate_limit_register_window_seconds,
    )
    register_user(
        db,
        email=req.email,
        password=req.password,
        name=req.name,
        zip_code=req.zip_code,
        state_abbr=req.state_abbr,
    )
    return {"message": "Account created! Check your email to confirm your address."}


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email_endpoint(body: VerifyEmailRequest, db: Client = Depends(get_db)):
    verify_email(db, token=body.token)
    return {"message": "Email confirmed! You can now log in."}


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_endpoint(
    body: ResendVerificationRequest,
    request: Request,
    db: Client = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(db, key=f"resend:{client_ip}", action="resend_verification", max_attempts=3, window_seconds=3600)
    resend_verification(db, email=body.email)
    return {"message": "If an unverified account exists, a new confirmation email was sent."}


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: Client = Depends(get_db)):
    s = get_settings()
    client_ip = request.client.host if request.client else "unknown"
    check_rate_limit(
        db,
        key=f"login:{client_ip}",
        action="login",
        max_attempts=s.rate_limit_login_max,
        window_seconds=s.rate_limit_login_window_seconds,
    )
    tokens = login_user(db, email=req.email, password=req.password)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: Client = Depends(get_db)):
    tokens = refresh_access_token(db, refresh_token=body.refresh_token)
    return tokens
