"""Auth business logic — all DB access is server-side with service_role.

Security invariants enforced here:
- user_id always comes from the verified JWT, never from request payload
- cross-tenant access returns 404, not 403 (don't leak existence)
- email not confirmed -> login blocked
- refresh tokens stored as SHA-256 hashes, never plaintext
"""
from datetime import datetime, timezone

from fastapi import HTTPException, status
from supabase import Client

from core.security import (
    create_access_token,
    email_confirm_expires_at,
    generate_email_confirm_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    refresh_token_expires_at,
    verify_password,
)
from schemas.auth import AuthResponse
from services.email_service import send_confirmation_email

# Pre-computed bcrypt hash used as a timing-attack constant when email not found.
# This ensures verify_password() always runs, preventing user enumeration via timing.
_TIMING_DUMMY_HASH = hash_password("timing_attack_constant_dummy_value_not_a_real_password")


# ── Registration ──────────────────────────────────────────────────────────────

def register_user(db: Client, email: str, password: str, full_name: str) -> dict:
    email = email.lower().strip()

    # Duplicate check — return generic message to avoid email enumeration
    existing = db.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Não foi possível criar a conta. Verifique os dados.",
        )

    confirm_token = generate_email_confirm_token()
    token_hash = hash_token(confirm_token)

    user_row = (
        db.table("users")
        .insert(
            {
                "email": email,
                "password_hash": hash_password(password),
                "email_confirmed": False,
                "email_confirm_token": token_hash,
                "email_confirm_expires": email_confirm_expires_at().isoformat(),
            }
        )
        .execute()
    )
    user_id = user_row.data[0]["id"]

    db.table("profiles").insert({"user_id": user_id, "full_name": full_name}).execute()

    send_confirmation_email(email, confirm_token)

    return {"user_id": user_id, "message": "Conta criada. Verifique seu email para confirmar."}


# ── Email confirmation ────────────────────────────────────────────────────────

def confirm_email(db: Client, raw_token: str) -> dict:
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc).isoformat()

    result = (
        db.table("users")
        .select("id, email_confirmed, email_confirm_expires")
        .eq("email_confirm_token", token_hash)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token inválido.")

    row = result.data[0]
    if row["email_confirmed"]:
        return {"message": "Email já confirmado."}

    if row["email_confirm_expires"] < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expirado.")

    db.table("users").update(
        {"email_confirmed": True, "email_confirm_token": None, "email_confirm_expires": None}
    ).eq("id", row["id"]).execute()

    return {"message": "Email confirmado com sucesso!"}


# ── Login ─────────────────────────────────────────────────────────────────────

_INVALID_CREDS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Email ou senha incorretos.",
)


def login_user(db: Client, email: str, password: str) -> AuthResponse:
    email = email.lower().strip()

    result = (
        db.table("users")
        .select("id, password_hash, email_confirmed")
        .eq("email", email)
        .execute()
    )

    # Always verify password even if not found — constant-time defence against timing attacks
    if not result.data:
        verify_password(password, _TIMING_DUMMY_HASH)
        raise _INVALID_CREDS

    row = result.data[0]
    if not verify_password(password, row["password_hash"]):
        raise _INVALID_CREDS

    if not row["email_confirmed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email não confirmado. Verifique sua caixa de entrada.",
        )

    return _issue_tokens(db, row["id"])


# ── Token refresh ─────────────────────────────────────────────────────────────

def refresh_tokens(db: Client, raw_refresh_token: str) -> AuthResponse:
    token_hash = hash_token(raw_refresh_token)
    now = datetime.now(timezone.utc).isoformat()

    result = (
        db.table("refresh_tokens")
        .select("id, user_id, expires_at, revoked_at")
        .eq("token_hash", token_hash)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    row = result.data[0]
    if row["revoked_at"] or row["expires_at"] < now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expirado ou revogado.")

    # Rotate: revoke old, issue new
    db.table("refresh_tokens").update({"revoked_at": now}).eq("id", row["id"]).execute()
    return _issue_tokens(db, row["user_id"])


# ── Logout ────────────────────────────────────────────────────────────────────

def logout_user(db: Client, user_id: str, raw_refresh_token: str) -> dict:
    token_hash = hash_token(raw_refresh_token)
    now = datetime.now(timezone.utc).isoformat()

    db.table("refresh_tokens").update({"revoked_at": now}).eq("token_hash", token_hash).eq(
        "user_id", user_id
    ).execute()
    return {"message": "Sessão encerrada."}


# ── Internal helpers ──────────────────────────────────────────────────────────

def _issue_tokens(db: Client, user_id: str) -> AuthResponse:
    raw_refresh = generate_refresh_token()
    db.table("refresh_tokens").insert(
        {
            "user_id": user_id,
            "token_hash": hash_token(raw_refresh),
            "expires_at": refresh_token_expires_at().isoformat(),
        }
    ).execute()
    return AuthResponse(
        access_token=create_access_token(user_id),
        refresh_token=raw_refresh,
        user_id=user_id,
    )
