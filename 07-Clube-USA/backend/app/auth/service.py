from datetime import datetime, timezone
from typing import Optional

from supabase import Client

from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    generate_refresh_token,
    generate_email_confirm_token,
    refresh_token_expires_at,
)
from app.email.service import send_confirmation_email


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_user(db: Client, email: str, password: str, full_name: str,
                  phone: str = "", zip_code: str = "") -> dict:
    """Creates user, sends confirmation email. Returns user row."""
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        # Generic error — don't leak whether email is registered
        raise AuthError("Não foi possível criar a conta. Tente novamente.", 400)

    confirm_token = generate_email_confirm_token()
    user_data = {
        "email": email,
        "password_hash": hash_password(password),
        "full_name": full_name,
        "phone": phone,
        "zip_code": zip_code,
        "email_confirmed": False,
        "email_confirm_token": confirm_token,
        "email_confirm_sent_at": datetime.now(timezone.utc).isoformat(),
    }
    result = db.table("users").insert(user_data).execute()
    if not result.data:
        raise AuthError("Erro interno ao criar conta.", 500)

    user = result.data[0]
    send_confirmation_email(email, full_name, confirm_token)
    return user


def confirm_email(db: Client, token: str) -> bool:
    """Marks email as confirmed. Returns True on success."""
    result = (
        db.table("users")
        .select("id, email_confirmed")
        .eq("email_confirm_token", token)
        .execute()
    )
    if not result.data:
        return False

    user = result.data[0]
    if user["email_confirmed"]:
        return True  # idempotent

    db.table("users").update({
        "email_confirmed": True,
        "email_confirm_token": None,
        "email_confirm_sent_at": None,
    }).eq("id", user["id"]).execute()
    return True


def login_user(db: Client, email: str, password: str) -> tuple[str, str]:
    """Returns (access_token, refresh_token) or raises AuthError."""
    result = db.table("users").select("*").eq("email", email).execute()
    if not result.data:
        raise AuthError("Credenciais inválidas.", 401)

    user = result.data[0]
    if not verify_password(password, user["password_hash"]):
        raise AuthError("Credenciais inválidas.", 401)

    if not user["email_confirmed"]:
        raise AuthError("Confirme seu email antes de fazer login.", 403)

    return _issue_tokens(db, user["id"])


def refresh_tokens(db: Client, raw_refresh_token: str) -> tuple[str, str]:
    """Validates refresh token, issues new pair. One-time-use."""
    now = datetime.now(timezone.utc)
    result = (
        db.table("refresh_tokens")
        .select("*")
        .eq("token", raw_refresh_token)
        .is_("used_at", "null")
        .gt("expires_at", now.isoformat())
        .execute()
    )
    if not result.data:
        raise AuthError("Refresh token inválido ou expirado.", 401)

    rt = result.data[0]
    # Mark as used immediately (one-time-use)
    db.table("refresh_tokens").update({"used_at": now.isoformat()}).eq("id", rt["id"]).execute()

    return _issue_tokens(db, rt["user_id"])


def _issue_tokens(db: Client, user_id: str) -> tuple[str, str]:
    access_token = create_access_token(user_id)
    raw_refresh = generate_refresh_token()
    db.table("refresh_tokens").insert({
        "user_id": user_id,
        "token": raw_refresh,
        "expires_at": refresh_token_expires_at().isoformat(),
    }).execute()
    return access_token, raw_refresh


def get_user_by_id(db: Client, user_id: str) -> Optional[dict]:
    result = db.table("users").select(
        "id, email, email_confirmed, full_name, phone, zip_code, city, state, created_at"
    ).eq("id", user_id).execute()
    return result.data[0] if result.data else None
