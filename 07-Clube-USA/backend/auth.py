import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from db import get_db
from email_service import send_confirmation_email
from limiter import limiter
from models import LoginRequest, ProfileUpdate, RegisterRequest, UserProfile
from security import (
    _DUMMY_HASH,
    create_access_token,
    generate_confirmation_token,
    get_current_user_id,
    hash_password,
    verify_password,
)

router = APIRouter()

_COOKIE_NAME = "access_token"
_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
_COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN") or None


def _set_auth_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        max_age=7 * 24 * 3600,
        domain=_COOKIE_DOMAIN,
    )


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterRequest):
    db = get_db()

    existing = (
        db.table("users")
        .select("id")
        .eq("email", body.email.lower())
        .execute()
    )
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Este email já está cadastrado",
        )

    confirmation_token = generate_confirmation_token()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(hours=24)
    ).isoformat()

    result = (
        db.table("users")
        .insert(
            {
                "email": body.email.lower(),
                "password_hash": hash_password(body.password),
                "first_name": body.first_name,
                "last_name": body.last_name,
                "zip_code": body.zip_code,
                "email_confirmed": False,
                "confirmation_token": confirmation_token,
                "confirmation_expires_at": expires_at,
            }
        )
        .execute()
    )

    user = result.data[0]

    try:
        send_confirmation_email(user["email"], confirmation_token, user["first_name"])
    except Exception:
        # Registration succeeds even if email fails; the confirmation link
        # is logged to stdout in dev mode via email_service.
        pass

    return {"message": "Cadastro realizado! Verifique seu email para confirmar a conta."}


@router.get("/confirm-email")
async def confirm_email(token: str):
    db = get_db()

    result = (
        db.table("users")
        .select("id, confirmation_expires_at, email_confirmed")
        .eq("confirmation_token", token)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou já utilizado",
        )

    user = result.data[0]

    if user["email_confirmed"]:
        return {"message": "Email já confirmado anteriormente. Você pode fazer login."}

    expires_str = user["confirmation_expires_at"]
    expires_at = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token expirado. Solicite um novo email de confirmação.",
        )

    db.table("users").update(
        {
            "email_confirmed": True,
            "confirmation_token": None,
            "confirmation_expires_at": None,
        }
    ).eq("id", user["id"]).execute()

    return {"message": "Email confirmado com sucesso! Você já pode fazer login."}


@router.post("/resend-confirmation", status_code=status.HTTP_200_OK)
@limiter.limit("3/minute")
async def resend_confirmation(request: Request, body: LoginRequest):
    """Re-sends confirmation email. Uses LoginRequest (email + password)
    to authenticate the request without issuing a session token."""
    db = get_db()

    result = (
        db.table("users")
        .select("id, email, first_name, email_confirmed, password_hash")
        .eq("email", body.email.lower())
        .execute()
    )

    user = result.data[0] if result.data else None
    check_hash = user["password_hash"] if user else _DUMMY_HASH
    password_ok = verify_password(body.password, check_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if user["email_confirmed"]:
        return {"message": "Email já confirmado. Faça login normalmente."}

    new_token = generate_confirmation_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    db.table("users").update(
        {
            "confirmation_token": new_token,
            "confirmation_expires_at": expires_at,
        }
    ).eq("id", user["id"]).execute()

    try:
        send_confirmation_email(user["email"], new_token, user["first_name"])
    except Exception:
        pass

    return {"message": "Email de confirmação reenviado. Verifique sua caixa de entrada."}


@router.post("/login")
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, response: Response):
    db = get_db()

    result = (
        db.table("users")
        .select("id, email, first_name, last_name, zip_code, email_confirmed, password_hash")
        .eq("email", body.email.lower())
        .execute()
    )

    user = result.data[0] if result.data else None
    # Always run bcrypt to prevent user-enumeration via timing
    check_hash = user["password_hash"] if user else _DUMMY_HASH
    password_ok = verify_password(body.password, check_hash)

    if not user or not password_ok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
        )

    if not user["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada ou solicite o reenvio.",
        )

    token = create_access_token(user["id"])
    _set_auth_cookie(response, token)

    return {
        "message": "Login realizado com sucesso",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "zip_code": user.get("zip_code"),
        },
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=_COOKIE_NAME,
        httponly=True,
        secure=_COOKIE_SECURE,
    )
    return {"message": "Logout realizado com sucesso"}


@router.get("/me", response_model=UserProfile)
async def get_me(user_id: str = Depends(get_current_user_id)):
    db = get_db()

    result = (
        db.table("users")
        .select("id, email, first_name, last_name, zip_code, email_confirmed, created_at")
        .eq("id", user_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return result.data[0]


@router.put("/profile")
async def update_profile(
    body: ProfileUpdate,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()

    updates = {}
    if body.first_name is not None:
        updates["first_name"] = body.first_name
    if body.last_name is not None:
        updates["last_name"] = body.last_name
    if body.zip_code is not None:
        updates["zip_code"] = body.zip_code

    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nenhum campo para atualizar",
        )

    # .eq("id", user_id) ensures we only update the authenticated user's record (no IDOR)
    result = db.table("users").update(updates).eq("id", user_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return {"message": "Perfil atualizado com sucesso"}
