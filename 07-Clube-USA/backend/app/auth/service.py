import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.config import get_settings
from app.db import get_db
from app.email import send_confirmation_email
from app.security import (
    create_access_token,
    generate_confirmation_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)

logger = logging.getLogger(__name__)


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def register_user(email: str, password: str, full_name: str) -> dict:
    db = get_db()

    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise AuthError("Email ja cadastrado", 409)

    pw_hash = hash_password(password)
    result = db.table("users").insert({
        "email": email,
        "password_hash": pw_hash,
        "full_name": full_name,
        "email_confirmed": False,
    }).execute()
    user = result.data[0]
    user_id = user["id"]

    token = generate_confirmation_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    db.table("email_confirmations").insert({
        "user_id": user_id,
        "token": token,
        "expires_at": expires_at,
    }).execute()

    sent = send_confirmation_email(email, token, full_name)
    if not sent:
        logger.warning("Confirmation email not sent for user %s (SMTP not configured)", user_id)

    return {"user_id": user_id, "email": email, "email_sent": sent}


def login_user(email: str, password: str) -> dict:
    db = get_db()
    s = get_settings()

    result = db.table("users").select("*").eq("email", email).eq("is_active", True).execute()
    if not result.data:
        raise AuthError("Email ou senha incorretos", 401)

    user = result.data[0]

    if not verify_password(password, user["password_hash"]):
        raise AuthError("Email ou senha incorretos", 401)

    if not user["email_confirmed"]:
        raise AuthError(
            "Confirme seu email antes de fazer login. Verifique sua caixa de entrada.",
            403,
        )

    access_token = create_access_token(user["id"], s.access_token_expire_minutes)
    raw_refresh, refresh_hash = generate_refresh_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(days=s.refresh_token_expire_days)).isoformat()

    db.table("refresh_tokens").insert({
        "user_id": user["id"],
        "token_hash": refresh_hash,
        "expires_at": expires_at,
    }).execute()

    db.table("users").update({
        "last_login_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", user["id"]).execute()

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh,
        "user_id": user["id"],
        "email_confirmed": True,
    }


def confirm_email(token: str) -> dict:
    db = get_db()
    now = datetime.now(timezone.utc)

    result = db.table("email_confirmations").select("*").eq("token", token).execute()
    if not result.data:
        raise AuthError("Token invalido", 400)

    conf = result.data[0]

    if conf["used_at"]:
        raise AuthError("Token ja utilizado", 400)

    expires_at = _parse_dt(conf["expires_at"])
    if now > expires_at:
        raise AuthError("Token expirado. Solicite um novo email de confirmacao.", 400)

    db.table("email_confirmations").update({
        "used_at": now.isoformat()
    }).eq("id", conf["id"]).execute()

    db.table("users").update({
        "email_confirmed": True
    }).eq("id", conf["user_id"]).execute()

    return {"message": "Email confirmado com sucesso!"}


def resend_confirmation(email: str) -> dict:
    """Always returns a neutral message to avoid email enumeration."""
    neutral = {"message": "Se o email existir e nao estiver confirmado, um novo link foi enviado."}
    db = get_db()

    result = db.table("users").select("*").eq("email", email).execute()
    if not result.data:
        return neutral

    user = result.data[0]
    if user["email_confirmed"]:
        return neutral

    # Invalidate existing unused tokens
    db.table("email_confirmations").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("user_id", user["id"]).is_("used_at", "null").execute()

    token = generate_confirmation_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    db.table("email_confirmations").insert({
        "user_id": user["id"],
        "token": token,
        "expires_at": expires_at,
    }).execute()

    send_confirmation_email(email, token, user["full_name"])
    return neutral


def refresh_access_token(raw_refresh: str) -> dict:
    db = get_db()
    s = get_settings()
    now = datetime.now(timezone.utc)

    token_hash = hash_refresh_token(raw_refresh)
    result = db.table("refresh_tokens").select("*").eq("token_hash", token_hash).execute()
    if not result.data:
        raise AuthError("Refresh token invalido", 401)

    rt = result.data[0]
    if rt["revoked_at"]:
        raise AuthError("Refresh token revogado", 401)

    if now > _parse_dt(rt["expires_at"]):
        raise AuthError("Refresh token expirado", 401)

    # Rotate: revoke old, issue new
    db.table("refresh_tokens").update({
        "revoked_at": now.isoformat()
    }).eq("id", rt["id"]).execute()

    access_token = create_access_token(rt["user_id"], s.access_token_expire_minutes)
    raw_new, new_hash = generate_refresh_token()
    new_expires = (now + timedelta(days=s.refresh_token_expire_days)).isoformat()
    db.table("refresh_tokens").insert({
        "user_id": rt["user_id"],
        "token_hash": new_hash,
        "expires_at": new_expires,
    }).execute()

    user_res = db.table("users").select("email_confirmed").eq("id", rt["user_id"]).execute()

    return {
        "access_token": access_token,
        "refresh_token": raw_new,
        "user_id": rt["user_id"],
        "email_confirmed": user_res.data[0]["email_confirmed"],
    }


def _parse_dt(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
