from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import Database, DuplicateError
from app.dependencies import get_db, limit_login, limit_register, limit_resend
from app.models.user import MessageResponse, TokenResponse, UserLogin, UserProfile, UserRegister
from app.services.auth import create_access_token, hash_password, verify_password
from app.services.email import send_confirmation_email

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(limit_register)])
def register(body: UserRegister, db: Database = Depends(get_db)):
    try:
        user = db.create_user(
            email=body.email.lower(),
            password_hash=hash_password(body.password),
            full_name=body.full_name,
        )
    except DuplicateError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    token = db.create_confirmation_token(user["id"])
    send_confirmation_email(email=user["email"], full_name=user["full_name"], token=token)

    return {"message": "Cadastro realizado! Verifique seu e-mail para confirmar a conta."}


@router.post("/login", response_model=TokenResponse, dependencies=[Depends(limit_login)])
def login(body: UserLogin, db: Database = Depends(get_db)):
    user = db.get_user_by_email(body.email.lower())

    # Constant-time failure path — same error regardless of whether email exists
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos.",
        )

    if not user.get("is_active"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada.")

    token = create_access_token(user_id=user["id"], email=user["email"])
    return TokenResponse(access_token=token, user=UserProfile.from_db(user))


@router.get("/confirm-email", response_model=MessageResponse)
def confirm_email(token: str, db: Database = Depends(get_db)):
    record = db.get_confirmation_token(token)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link inválido ou já utilizado.",
        )

    expires_at_str = record["expires_at"]
    if isinstance(expires_at_str, str):
        expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
    else:
        expires_at = expires_at_str

    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Link expirado. Solicite um novo e-mail de confirmação.",
        )

    db.confirm_user_email(record["user_id"])
    db.mark_confirmation_token_used(record["id"])

    return {"message": "E-mail confirmado com sucesso! Você já pode fazer login."}


@router.post("/resend-confirmation", response_model=MessageResponse,
             dependencies=[Depends(limit_resend)])
def resend_confirmation(body: UserLogin, db: Database = Depends(get_db)):
    """Requires correct password to prevent confirmation-link harvesting."""
    user = db.get_user_by_email(body.email.lower())

    if not user or not verify_password(body.password, user["password_hash"]):
        return {"message": "Se a conta existir, um novo e-mail de confirmação será enviado."}

    if user.get("email_confirmed"):
        return {"message": "Seu e-mail já está confirmado."}

    if db.count_recent_confirmations(user["id"], since_hours=1) >= 3:
        return {"message": "Muitas solicitações. Tente novamente em 1 hora."}

    token = db.create_confirmation_token(user["id"])
    send_confirmation_email(email=user["email"], full_name=user["full_name"], token=token)
    return {"message": "Se a conta existir, um novo e-mail de confirmação será enviado."}
