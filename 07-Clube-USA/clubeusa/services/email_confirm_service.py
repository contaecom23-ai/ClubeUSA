# ============================================================
#  services/email_confirm_service.py — Clube USA
#  Fase 0.1: confirmação de email
# ============================================================

import os
import logging
from datetime import datetime, timedelta, timezone

from utils.security import decrypt
from utils.email import generate_confirm_token, send_email_confirmation, _hash_token

log = logging.getLogger("email_confirm_service")

_TTL_HOURS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def request_email_confirmation(member_id: str) -> bool:
    """
    Gera token de confirmação, persiste hash no banco e envia email.
    Retorna True se email foi enviado (ou logado em dev), False se membro não tem email.
    Idempotente: sobrescreve token anterior do mesmo membro.
    """
    sb = _supabase()

    result = sb.table("members").select(
        "email_enc,email_verified,language"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro não encontrado.")

    m = result.data[0]

    if not m.get("email_enc"):
        return False  # membro não tem email cadastrado

    if m.get("email_verified"):
        return True   # já confirmado — noop silencioso

    email = decrypt(m["email_enc"])
    token, token_hash = generate_confirm_token()
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=_TTL_HOURS)).isoformat()

    # Upsert: remove token anterior do mesmo membro, insere novo
    sb.table("email_confirm_tokens").delete().eq("member_id", member_id).execute()
    sb.table("email_confirm_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    send_email_confirmation(email, member_id, token, m.get("language", "pt"))
    return True


def verify_email_confirmation(token: str) -> dict:
    """
    Verifica token de confirmação.
    Retorna {"ok": True, "member_id": "..."} ou lança ValueError.
    """
    from datetime import timezone as _tz

    if not token or len(token) > 128:
        raise ValueError("Token inválido.")

    token_hash = _hash_token(token)
    sb = _supabase()

    result = sb.table("email_confirm_tokens").select("*").eq(
        "token_hash", token_hash
    ).execute()

    if not result.data:
        raise ValueError("Token inválido ou expirado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token já utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=_tz.utc)
    if datetime.now(_tz.utc) > expires:
        sb.table("email_confirm_tokens").delete().eq("id", record["id"]).execute()
        raise ValueError("Token expirado. Solicite um novo link.")

    member_id = record["member_id"]

    # Marca token como usado e email como verificado — atomicamente via updates sequenciais
    # (Supabase não suporta transações no client SDK; risco de inconsistência é baixo aqui)
    sb.table("email_confirm_tokens").update({
        "used_at": datetime.now(_tz.utc).isoformat()
    }).eq("id", record["id"]).execute()

    sb.table("members").update({
        "email_verified": True
    }).eq("id", member_id).execute()

    sb.table("audit_logs").insert({
        "actor_type":  "member",
        "actor_id":    member_id,
        "action":      "member.email_verified",
        "target_type": "member",
        "target_id":   member_id,
        "metadata":    {},
    }).execute()

    log.info(f"Email confirmado para membro {member_id}")
    return {"ok": True, "member_id": member_id}
