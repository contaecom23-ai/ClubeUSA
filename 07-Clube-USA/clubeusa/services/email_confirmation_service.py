# ============================================================
#  services/email_confirmation_service.py — Clube USA
#  Fase 0.1 — Confirmação de email
# ============================================================

import logging
import os
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_confirmation_service")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def save_email_token(email_hash: str, token: str, ttl_sec: int = 86400) -> None:
    """Salva token de confirmação de email. Sobrescreve token anterior do mesmo email."""
    sb = _supabase()
    sb.table("email_tokens").delete().eq("email_hash", email_hash).execute()
    sb.table("email_tokens").insert({
        "email_hash": email_hash,
        "token":      token,
        "expires_at": (datetime.utcnow() + timedelta(seconds=ttl_sec)).isoformat(),
    }).execute()


def verify_email_token(email_hash: str, token: str) -> tuple:
    """
    Verifica token — retorna (True, '') ou (False, mensagem_erro).
    Deleta o token após verificação bem-sucedida (single-use).
    """
    sb = _supabase()

    result = sb.table("email_tokens").select("*").eq("email_hash", email_hash).execute()
    if not result.data:
        return False, "Codigo invalido ou expirado."

    record = result.data[0]

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        sb.table("email_tokens").delete().eq("email_hash", email_hash).execute()
        return False, "Codigo expirado. Solicite um novo."

    if record["attempts"] >= 5:
        sb.table("email_tokens").delete().eq("email_hash", email_hash).execute()
        return False, "Muitas tentativas. Solicite novo codigo."

    if record["token"] != token.strip():
        sb.table("email_tokens").update(
            {"attempts": record["attempts"] + 1}
        ).eq("email_hash", email_hash).execute()
        return False, "Codigo incorreto."

    sb.table("email_tokens").delete().eq("email_hash", email_hash).execute()
    return True, ""


def set_email_confirmed(member_id: str) -> None:
    """Marca email_confirmed = TRUE no banco e registra audit log."""
    sb = _supabase()
    sb.table("members").update({"email_confirmed": True}).eq("id", member_id).execute()
    sb.table("audit_logs").insert({
        "actor_id":    member_id,
        "actor_type":  "member",
        "action":      "member.email_confirmed",
        "target_type": "member",
        "target_id":   member_id,
    }).execute()
    log.info(f"Email confirmado para membro {member_id}")
