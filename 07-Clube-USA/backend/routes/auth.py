from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from auth_utils import (
    create_access_token,
    email_token_expiry,
    generate_email_token,
    get_dummy_hash,
    hash_password,
    verify_password,
)
from config import get_settings
from database import get_db
from email_service import send_confirmation_email
from models import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


# ------------------------------------------------------------------ Register
def _register_route(request: Request, body: RegisterRequest) -> TokenResponse:
    db = get_db()
    s = get_settings()

    # Verificar email duplicado
    existing = db.table("users").select("id").eq("email", body.email).execute()
    if existing.data:
        # Não revelar se existe ou não — retornar 409 genérico
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email já cadastrado")

    token = generate_email_token()
    expires = email_token_expiry()

    # Inserir usuário
    user_row = (
        db.table("users")
        .insert(
            {
                "email": body.email,
                "password_hash": hash_password(body.password),
                "confirmation_token": token,
                "confirmation_token_expires_at": expires.isoformat(),
            }
        )
        .execute()
    )
    user_id = user_row.data[0]["id"]

    # Criar perfil vazio vinculado
    db.table("profiles").insert({"user_id": user_id, "full_name": body.full_name}).execute()

    # Enviar email de confirmação
    confirm_url = f"{s.FRONTEND_URL}/confirmar-email.html?token={token}"
    send_confirmation_email(body.email, confirm_url)

    return TokenResponse(access_token=create_access_token(user_id))


# ------------------------------------------------------------------ Confirm email
def _confirm_email_route(token: str) -> dict:
    db = get_db()

    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token ausente")

    rows = (
        db.table("users")
        .select("id, is_email_confirmed, confirmation_token_expires_at")
        .eq("confirmation_token", token)
        .execute()
    )

    if not rows.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido")

    user = rows.data[0]

    if user["is_email_confirmed"]:
        return {"message": "Email já confirmado"}

    expires_at = datetime.fromisoformat(user["confirmation_token_expires_at"])
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado")

    db.table("users").update(
        {
            "is_email_confirmed": True,
            "confirmation_token": None,
            "confirmation_token_expires_at": None,
        }
    ).eq("id", user["id"]).execute()

    return {"message": "Email confirmado com sucesso"}


# ------------------------------------------------------------------ Login
def _login_route(request: Request, body: LoginRequest) -> TokenResponse:
    db = get_db()

    rows = db.table("users").select("id, password_hash").eq("email", body.email).execute()

    # Tempo constante mesmo se usuário não existe (evitar timing attack por enumeração)
    stored_hash = rows.data[0]["password_hash"] if rows.data else get_dummy_hash()
    password_ok = verify_password(body.password, stored_hash)

    if not rows.data or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    return TokenResponse(access_token=create_access_token(rows.data[0]["id"]))


# ------------------------------------------------------------------ Route registration (with rate limiting)
# Os decorators são aplicados no main.py via limiter para poder injetar o objeto
# aqui exportamos as funções handler
register_handler = _register_route
confirm_email_handler = _confirm_email_route
login_handler = _login_route
