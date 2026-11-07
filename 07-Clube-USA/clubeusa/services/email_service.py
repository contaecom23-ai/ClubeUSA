# ============================================================
#  services/email_service.py — Clube USA
#  Confirmacao de email: gera token, verifica, marca confirmado
# ============================================================

import os
import secrets
import logging
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

_TOKEN_TTL_HOURS = 24
_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def request_email_verification(member_id: str) -> dict:
    """
    Gera token de verificacao de email e "envia" por email.

    Em dev: loga o link de verificacao.
    Em producao: requer RESEND_API_KEY (ver DECISOES.md #0001).

    Retorna {"sent": bool, "expires_in_hours": int}.
    Levanta ValueError se membro nao tem email cadastrado.
    """
    sb = _supabase()

    result = sb.table("members").select(
        "id,email_enc,email_confirmed_at"
    ).eq("id", member_id).execute()

    if not result.data:
        raise ValueError("Membro nao encontrado.")

    m = result.data[0]
    if not m.get("email_enc"):
        raise ValueError("Nenhum email cadastrado. Atualize seu perfil primeiro.")

    # Invalida tokens anteriores nao usados do mesmo membro
    sb.table("email_tokens").delete().eq("member_id", member_id).is_("used_at", "null").execute()

    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)

    sb.table("email_tokens").insert({
        "member_id":  member_id,
        "token":      token,
        "expires_at": expires_at.isoformat(),
    }).execute()

    verify_url = f"{_APP_URL}/auth/email/verify/{token}"

    if os.environ.get("ENVIRONMENT") == "production":
        _send_verification_email(m["email_enc"], verify_url)
    else:
        log.info(f"[DEV] Link de verificacao de email para membro {member_id}: {verify_url}")

    return {
        "sent":             True,
        "expires_in_hours": _TOKEN_TTL_HOURS,
        "dev_link":         verify_url if os.environ.get("ENVIRONMENT") != "production" else None,
    }


def verify_email_token(token: str) -> dict:
    """
    Verifica token e marca email como confirmado.

    Retorna {"confirmed": True, "member_id": str} ou levanta ValueError.
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)

    result = sb.table("email_tokens").select("*").eq("token", token).execute()
    if not result.data:
        raise ValueError("Token invalido ou expirado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token ja utilizado.")

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if now > expires:
        raise ValueError("Token expirado. Solicite um novo link de verificacao.")

    member_id = record["member_id"]

    # Marca o token como usado e confirma o email
    sb.table("email_tokens").update({"used_at": now.isoformat()}).eq("id", record["id"]).execute()
    sb.table("members").update(
        {"email_confirmed_at": now.isoformat()}
    ).eq("id", member_id).execute()

    # Audit
    try:
        sb.table("audit_logs").insert({
            "actor_type":  "member",
            "actor_id":    member_id,
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   member_id,
        }).execute()
    except Exception as e:
        log.warning(f"Audit log falhou: {e}")

    log.info(f"Email confirmado para membro {member_id}")
    return {"confirmed": True, "member_id": member_id}


def _send_verification_email(email_enc: str, verify_url: str):
    """
    Envia email de confirmacao via Resend (provider configurado via RESEND_API_KEY).
    Se a chave nao estiver presente, loga aviso e retorna — nao lanca excecao
    para nao bloquear o cadastro.
    """
    from utils.security import decrypt

    api_key = os.environ.get("RESEND_API_KEY")
    if not api_key:
        log.warning("RESEND_API_KEY nao configurada. Email de confirmacao nao enviado.")
        return

    try:
        email = decrypt(email_enc)
        import requests as req
        resp = req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from":    "Clube USA <noreply@clubeusa.com>",
                "to":      [email],
                "subject": "Confirme seu email — Clube USA",
                "html": (
                    f"<p>Ola! Clique no link abaixo para confirmar seu email no Clube USA:</p>"
                    f"<p><a href='{verify_url}'>{verify_url}</a></p>"
                    f"<p>Este link expira em {_TOKEN_TTL_HOURS} horas.</p>"
                    f"<p>Se voce nao solicitou isso, ignore este email.</p>"
                ),
            },
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            log.warning(f"Resend retornou {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        log.warning(f"Falha ao enviar email de verificacao: {e}")
