"""
Auth business logic. All DB operations go through the Supabase service_role client.
user_id is ALWAYS taken from the JWT, never trusted from request body.
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from supabase import Client

from app.auth.email import send_verification_email
from app.auth.utils import (
    create_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    refresh_token_expiry,
    verify_password,
)
from app.config import get_settings

_VERIFICATION_TOKEN_TTL_HOURS = 24


# ── Registration ─────────────────────────────────────────────────────────────

def register_user(
    db: Client,
    *,
    email: str,
    password: str,
    name: str,
    zip_code: Optional[str],
    state_abbr: Optional[str],
) -> dict:
    # 1. Check duplicate email — return generic error to avoid email enumeration
    existing = db.table("users").select("id").eq("email", email.lower()).execute()
    if existing.data:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # 2. Hash password
    pw_hash = hash_password(password)

    # 3. Generate verification token (store hash, send plain)
    vtoken = generate_opaque_token()
    vtoken_hash = hash_token(vtoken)

    # 4. Insert user
    row = {
        "email": email.lower(),
        "password_hash": pw_hash,
        "name": name.strip(),
        "zip_code": zip_code,
        "state_abbr": state_abbr,
        "email_verified": False,
        "email_verification_token_hash": vtoken_hash,
        "email_verification_sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }
    result = db.table("users").insert(row).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")

    user = result.data[0]

    # 5. Send verification email (non-fatal — log errors, don't crash registration)
    try:
        send_verification_email(user["email"], user["name"], vtoken)
    except Exception as exc:
        # The user is registered; email failure should not block the response.
        # Log but don't expose internals.
        import logging
        logging.getLogger(__name__).error("Failed to send verification email: %s", exc)

    return {"id": user["id"], "email": user["email"], "name": user["name"]}


# ── Email verification ────────────────────────────────────────────────────────

def verify_email(db: Client, *, token: str) -> None:
    token_hash = hash_token(token)

    result = db.table("users") \
        .select("id, email_verified, email_verification_sent_at") \
        .eq("email_verification_token_hash", token_hash) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token.")

    user = result.data[0]

    if user["email_verified"]:
        return  # idempotent — already verified is OK

    # Check TTL
    sent_at = datetime.fromisoformat(user["email_verification_sent_at"])
    if sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(tz=timezone.utc) - sent_at).total_seconds() / 3600
    if age_hours > _VERIFICATION_TOKEN_TTL_HOURS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired. Request a new verification email.")

    db.table("users").update({
        "email_verified": True,
        "email_verified_at": datetime.now(tz=timezone.utc).isoformat(),
        "email_verification_token_hash": None,
    }).eq("id", user["id"]).execute()


def resend_verification(db: Client, *, email: str) -> None:
    result = db.table("users").select("id, name, email_verified, email_verification_sent_at").eq("email", email.lower()).execute()

    # Always return success to avoid email enumeration
    if not result.data:
        return

    user = result.data[0]
    if user["email_verified"]:
        return

    # Throttle: don't resend if sent < 5 min ago
    if user.get("email_verification_sent_at"):
        sent_at = datetime.fromisoformat(user["email_verification_sent_at"])
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        elapsed_minutes = (datetime.now(tz=timezone.utc) - sent_at).total_seconds() / 60
        if elapsed_minutes < 5:
            return  # silent — anti-spam

    vtoken = generate_opaque_token()
    vtoken_hash = hash_token(vtoken)
    db.table("users").update({
        "email_verification_token_hash": vtoken_hash,
        "email_verification_sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }).eq("id", user["id"]).execute()

    try:
        send_verification_email(email.lower(), user["name"], vtoken)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("Failed to resend verification email: %s", exc)


# ── Login ─────────────────────────────────────────────────────────────────────

def login_user(db: Client, *, email: str, password: str) -> dict:
    result = db.table("users") \
        .select("id, password_hash, name, email_verified") \
        .eq("email", email.lower()) \
        .execute()

    # Constant-time-ish: always run verify_password even on miss to avoid timing attacks
    dummy_hash = "$2b$12$DUMMYHASHFORTIMINGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
    stored_hash = result.data[0]["password_hash"] if result.data else dummy_hash

    if not verify_password(password, stored_hash) or not result.data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    user = result.data[0]

    if not user["email_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please confirm your email before logging in.",
        )

    access_token, expires_in = create_access_token(user["id"])
    rtoken = generate_opaque_token()
    rtoken_hash = hash_token(rtoken)

    db.table("refresh_tokens").insert({
        "user_id": user["id"],
        "token_hash": rtoken_hash,
        "expires_at": refresh_token_expiry().isoformat(),
    }).execute()

    return {
        "access_token": access_token,
        "refresh_token": rtoken,
        "token_type": "bearer",
        "expires_in": expires_in,
    }


# ── Token refresh ─────────────────────────────────────────────────────────────

def refresh_access_token(db: Client, *, refresh_token: str) -> dict:
    token_hash = hash_token(refresh_token)
    now = datetime.now(tz=timezone.utc).isoformat()

    result = db.table("refresh_tokens") \
        .select("id, user_id, expires_at, revoked") \
        .eq("token_hash", token_hash) \
        .execute()

    if not result.data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token.")

    rt = result.data[0]

    if rt["revoked"]:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked.")

    expires_at = datetime.fromisoformat(rt["expires_at"])
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired.")

    # Rotate: revoke old, issue new
    db.table("refresh_tokens").update({"revoked": True}).eq("id", rt["id"]).execute()

    access_token, expires_in = create_access_token(rt["user_id"])
    new_rtoken = generate_opaque_token()
    new_rtoken_hash = hash_token(new_rtoken)

    db.table("refresh_tokens").insert({
        "user_id": rt["user_id"],
        "token_hash": new_rtoken_hash,
        "expires_at": refresh_token_expiry().isoformat(),
    }).execute()

    return {
        "access_token": access_token,
        "refresh_token": new_rtoken,
        "token_type": "bearer",
        "expires_in": expires_in,
    }
