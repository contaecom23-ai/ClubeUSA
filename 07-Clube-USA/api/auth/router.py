from fastapi import APIRouter, BackgroundTasks, Depends, Request
from supabase import Client

from ..database import get_db
from ..limiter import limiter
from .email import send_confirmation_email
from .schemas import (
    ConfirmEmailRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResendConfirmationRequest,
    TokenResponse,
)
from .service import (
    confirm_email,
    create_access_token,
    login_user,
    register_user,
    resend_confirmation,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=201)
@limiter.limit("5/minute")
def register(
    request: Request,
    body: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db),
):
    user, token = register_user(db, body.email, body.password, body.full_name, body.zip_code)
    background_tasks.add_task(send_confirmation_email, body.email, token)
    return {"message": "Cadastro realizado! Verifique seu email para confirmar a conta."}


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(
    request: Request,
    body: LoginRequest,
    db: Client = Depends(get_db),
):
    user = login_user(db, body.email, body.password)
    access_token = create_access_token(user["id"])
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user["id"]),
        "email_confirmed": user["email_confirmed"],
    }


@router.post("/confirm-email", response_model=MessageResponse)
def confirm_email_route(body: ConfirmEmailRequest, db: Client = Depends(get_db)):
    confirm_email(db, body.token)
    return {"message": "Email confirmado com sucesso! Você já pode fazer login."}


@router.post("/resend-confirmation", response_model=MessageResponse)
@limiter.limit("3/minute")
def resend_confirmation_route(
    request: Request,
    body: ResendConfirmationRequest,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db),
):
    result = resend_confirmation(db, body.email)
    if result:
        token, _ = result
        background_tasks.add_task(send_confirmation_email, body.email, token)
    # Always return 200 to avoid email enumeration
    return {
        "message": (
            "Se o email existir e não estiver confirmado, "
            "um novo link de confirmação foi enviado."
        )
    }
