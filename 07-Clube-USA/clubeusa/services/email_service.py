# ============================================================
#  services/email_service.py — Clube USA
#  Confirmacao de email: geracao de token, verificacao e envio.
#
#  Em DEV: apenas loga o link (nao envia email real).
#  Em PROD: usa EMAIL_PROVIDER=resend ou sendgrid.
#
#  Decisao de provedor: ver DECISOES.md (2026-09-15).
# ============================================================

import os
import logging
import secrets
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

_TOKEN_TTL_HOURS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def request_email_confirmation(member_id: str, email: str) -> str:
    """
    Gera token seguro, persiste no banco com TTL de 24h e envia email.
    Invalida tokens anteriores nao utilizados do mesmo membro.
    Retorna o token gerado (util para testes).
    """
    sb = _supabase()

    # Invalida tokens anteriores nao usados do mesmo membro
    sb.table("email_confirmation_tokens").delete().eq("member_id", member_id).is_("used_at", "null").execute()

    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_TTL_HOURS)

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token":      token,
        "expires_at": expires.isoformat(),
    }).execute()

    _send_confirmation_email(email, token)
    log.info(f"Token de confirmacao gerado para membro {member_id}")
    return token


def confirm_email_token(token: str) -> dict:
    """
    Verifica token e marca email como confirmado no membro.
    Retorna {"ok": True, "member_id": str} ou levanta ValueError com mensagem.
    """
    sb = _supabase()
    now = datetime.now(timezone.utc)

    result = sb.table("email_confirmation_tokens").select("*").eq("token", token).execute()
    if not result.data:
        raise ValueError("Token invalido ou ja utilizado.")

    record = result.data[0]

    if record.get("used_at"):
        raise ValueError("Token ja utilizado.")

    expires_raw = record["expires_at"]
    expires = datetime.fromisoformat(expires_raw.replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if now > expires:
        raise ValueError("Token expirado. Solicite um novo.")

    member_id = record["member_id"]

    # Marca token como usado
    sb.table("email_confirmation_tokens").update({
        "used_at": now.isoformat()
    }).eq("id", record["id"]).execute()

    # Marca email como confirmado no membro
    sb.table("members").update({"email_confirmed": True}).eq("id", member_id).execute()

    try:
        sb.table("audit_logs").insert({
            "actor_type":  "system",
            "action":      "member.email_confirmed",
            "target_type": "member",
            "target_id":   member_id,
        }).execute()
    except Exception:
        pass

    log.info(f"Email confirmado para membro {member_id}")
    return {"ok": True, "member_id": member_id}


def _send_confirmation_email(email: str, token: str):
    """
    Envia email de confirmacao via provedor configurado.
    Em DEV: apenas loga o link (EMAIL_PROVIDER nao configurado ou ENVIRONMENT != production).
    Em PROD: usa EMAIL_PROVIDER env var (resend | sendgrid).
    """
    app_url = os.environ.get("APP_URL", "https://clubeusa.com")
    confirm_url = f"{app_url}/auth/email/confirm/{token}"

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Link de confirmacao de email: {confirm_url}")
        return

    provider = os.environ.get("EMAIL_PROVIDER", "")
    if provider == "resend":
        _send_via_resend(email, confirm_url)
    elif provider == "sendgrid":
        _send_via_sendgrid(email, confirm_url)
    else:
        log.warning(
            f"EMAIL_PROVIDER nao configurado em producao. "
            f"Configure EMAIL_PROVIDER=resend ou sendgrid. Token nao enviado para {email}."
        )


def _send_via_resend(email: str, confirm_url: str):
    try:
        import requests
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {os.environ['RESEND_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "from": os.environ.get("EMAIL_FROM", "Clube USA <noreply@clubeusa.com>"),
                "to": [email],
                "subject": "Confirme seu email — Clube USA",
                "html": _email_html(confirm_url),
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            log.error(f"Resend erro {resp.status_code}: {resp.text}")
    except Exception as e:
        log.error(f"Falha ao enviar via Resend: {e}")


def _send_via_sendgrid(email: str, confirm_url: str):
    try:
        import requests
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {os.environ['SENDGRID_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": email}]}],
                "from": {
                    "email": os.environ.get("EMAIL_FROM_ADDRESS", "noreply@clubeusa.com"),
                    "name": "Clube USA",
                },
                "subject": "Confirme seu email — Clube USA",
                "content": [{"type": "text/html", "value": _email_html(confirm_url)}],
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            log.error(f"SendGrid erro {resp.status_code}: {resp.text}")
    except Exception as e:
        log.error(f"Falha ao enviar via SendGrid: {e}")


def _email_html(confirm_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;background:#f9fafb">
  <div style="background:white;border-radius:8px;padding:32px;box-shadow:0 1px 3px rgba(0,0,0,.1)">
    <h2 style="color:#1a56db;margin-top:0">Clube USA — Confirme seu email</h2>
    <p style="color:#374151">Clique no botao abaixo para confirmar seu endereco de email:</p>
    <a href="{confirm_url}"
       style="display:inline-block;background:#1a56db;color:white;padding:12px 28px;
              border-radius:6px;text-decoration:none;font-weight:bold;font-size:16px">
      Confirmar email
    </a>
    <p style="color:#6b7280;font-size:13px;margin-top:24px">
      Link valido por 24 horas.<br>
      Se nao foi voce, ignore este email com seguranca.
    </p>
    <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
    <p style="color:#9ca3af;font-size:12px;margin:0">Clube USA &mdash; A comunidade brasileira nos EUA</p>
  </div>
</body>
</html>"""
