import secrets
from datetime import datetime, timedelta, timezone

from supabase import Client, create_client

from app.config import get_settings


class DuplicateError(Exception):
    pass


class Database:
    def __init__(self, client: Client) -> None:
        self._c = client

    # ── Users ──────────────────────────────────────────────────────────────

    def get_user_by_email(self, email: str) -> dict | None:
        result = self._c.table("users").select("*").eq("email", email).execute()
        return result.data[0] if result.data else None

    def get_user_by_id(self, user_id: str) -> dict | None:
        result = self._c.table("users").select("*").eq("id", user_id).execute()
        return result.data[0] if result.data else None

    def create_user(self, email: str, password_hash: str, full_name: str) -> dict:
        try:
            result = (
                self._c.table("users")
                .insert({"email": email, "password_hash": password_hash, "full_name": full_name})
                .execute()
            )
            return result.data[0]
        except Exception as exc:
            # Supabase wraps unique-constraint violations — detect by message
            if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
                raise DuplicateError("Email já cadastrado.") from exc
            raise

    def update_user_profile(self, user_id: str, data: dict) -> dict:
        result = (
            self._c.table("users")
            .update(data)
            .eq("id", user_id)
            .execute()
        )
        return result.data[0]

    def confirm_user_email(self, user_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._c.table("users").update(
            {"email_confirmed": True, "email_confirmed_at": now}
        ).eq("id", user_id).execute()

    # ── Email confirmations ────────────────────────────────────────────────

    def create_confirmation_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
        self._c.table("email_confirmations").insert(
            {"user_id": user_id, "token": token, "expires_at": expires_at}
        ).execute()
        return token

    def get_confirmation_token(self, token: str) -> dict | None:
        result = (
            self._c.table("email_confirmations")
            .select("*")
            .eq("token", token)
            .is_("used_at", "null")
            .execute()
        )
        return result.data[0] if result.data else None

    def mark_confirmation_token_used(self, token_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._c.table("email_confirmations").update({"used_at": now}).eq("id", token_id).execute()

    def count_recent_confirmations(self, user_id: str, since_hours: int = 1) -> int:
        since = (datetime.now(timezone.utc) - timedelta(hours=since_hours)).isoformat()
        result = (
            self._c.table("email_confirmations")
            .select("id", count="exact")
            .eq("user_id", user_id)
            .gte("created_at", since)
            .execute()
        )
        return result.count or 0


def build_db_client() -> Database:
    s = get_settings()
    client = create_client(s.supabase_url, s.supabase_service_role_key)
    return Database(client)
