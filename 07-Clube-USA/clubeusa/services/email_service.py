# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais (confirmacao de conta, etc.)
#
#  Configura via env vars:
#    EMAIL_PROVIDER   = "sendgrid" (default) | "smtp"
#    SENDGRID_API_KEY = sk-...
#    EMAIL_FROM       = no-reply@clubeusa.com
#    APP_URL          = https://clubeusa.com
#
#  Em desenvolvimento (ENVIRONMENT != "production"):
#    - Nao envia email real
#    - Loga o link de confirmacao no console
# ============================================================

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "no-reply@clubeusa.com")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Clube USA")
TOKEN_TTL_HRS = 24


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


# ============================================================
#  TOKEN MANAGEMENT
# ============================================================

def generate_confirmation_token() -> tuple[str, str]:
    """
    Retorna (raw_token, token_hash).
    raw_token vai no link do email.
    token_hash vai no banco — nunca o raw.
    """
    raw = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(raw.encode()).hexdigest()
    return raw, hashed


def store_confirmation_token(member_id: str, token_hash: str) -> None:
    """Persiste token de confirmacao no banco. Invalida tokens anteriores do mesmo membro."""
    sb = _supabase()
    # Invalida tokens anteriores nao usados (previne acumulo)
    sb.table("email_confirmation_tokens").delete().eq(
        "member_id", member_id
    ).is_("used_at", "null").execute()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=TOKEN_TTL_HRS)).isoformat(),
    }).execute()


def consume_confirmation_token(raw_token: str) -> str | None:
    """
    Valida e consome token de confirmacao.
    Retorna member_id se valido, None se invalido/expirado/ja usado.
    """
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    sb = _supabase()

    result = sb.table("email_confirmation_tokens").select(
        "id,member_id,expires_at,used_at"
    ).eq("token_hash", token_hash).execute()

    if not result.data:
        return None

    record = result.data[0]

    if record["used_at"] is not None:
        return None

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) > expires:
        return None

    # Marca como usado atomicamente
    sb.table("email_confirmation_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["id"]).execute()

    # Marca email como confirmado na tabela members
    sb.table("members").update({
        "email_confirmed_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["member_id"]).execute()

    return record["member_id"]


# ============================================================
#  ENVIO DE EMAIL
# ============================================================

def send_confirmation_email(member_id: str, email: str, raw_token: str) -> bool:
    """
    Envia email de confirmacao. Retorna True se enviou (ou logou em dev), False em erro.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm?token={raw_token}"

    subject = "Confirme seu email — Clube USA"
    html_body = _build_confirmation_html(confirm_url)
    text_body = (
        "Clube USA — Confirmacao de email\n\n"
        f"Clique no link abaixo para confirmar seu email (valido por {TOKEN_TTL_HRS} horas):\n\n"
        f"{confirm_url}\n\n"
        "Se voce nao criou uma conta no Clube USA, ignore este email."
    )

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Email de confirmacao para {email}: {confirm_url}")
        return True

    provider = os.environ.get("EMAIL_PROVIDER", "sendgrid").lower()
    if provider == "sendgrid":
        return _send_via_sendgrid(email, subject, html_body, text_body)

    log.warning(f"EMAIL_PROVIDER '{provider}' nao configurado. Link: {confirm_url}")
    return False


def _send_via_sendgrid(to_email: str, subject: str, html: str, text: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        log.warning("SENDGRID_API_KEY nao configurada — email nao enviado.")
        return False

    import urllib.request, urllib.error, json

    payload = json.dumps({
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": EMAIL_FROM, "name": EMAIL_FROM_NAME},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html",  "value": html},
        ],
    }).encode()

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            success = 200 <= resp.status < 300
            if not success:
                log.error(f"SendGrid retornou {resp.status}")
            return success
    except urllib.error.HTTPError as e:
        log.error(f"SendGrid HTTP error {e.code}: {e.read().decode()[:200]}")
        return False
    except Exception as e:
        log.error(f"Falha ao enviar email via SendGrid: {e}")
        return False


def _build_confirmation_html(confirm_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:sans-serif;background:#f4f4f4;margin:0;padding:20px">
  <table style="max-width:480px;margin:0 auto;background:#fff;border-radius:8px;overflow:hidden">
    <tr>
      <td style="background:#1a3a6c;padding:24px;text-align:center">
        <span style="color:#fff;font-size:22px;font-weight:700">🇧🇷 Clube USA</span>
      </td>
    </tr>
    <tr>
      <td style="padding:32px 24px">
        <h2 style="margin:0 0 16px;color:#1a3a6c">Confirme seu email</h2>
        <p style="color:#444;line-height:1.6">
          Obrigado por se cadastrar no <strong>Clube USA</strong>!<br>
          Clique no botao abaixo para confirmar seu endereco de email.
        </p>
        <div style="text-align:center;margin:32px 0">
          <a href="{confirm_url}"
             style="background:#1a3a6c;color:#fff;padding:14px 32px;border-radius:6px;
                    text-decoration:none;font-weight:700;display:inline-block">
            Confirmar email
          </a>
        </div>
        <p style="color:#888;font-size:13px;line-height:1.5">
          Link valido por {TOKEN_TTL_HRS} horas.<br>
          Se voce nao criou uma conta no Clube USA, ignore este email.<br><br>
          Ou copie e cole este link no navegador:<br>
          <a href="{confirm_url}" style="color:#1a3a6c;word-break:break-all">{confirm_url}</a>
        </p>
      </td>
    </tr>
    <tr>
      <td style="background:#f4f4f4;padding:16px;text-align:center;color:#aaa;font-size:12px">
        Clube USA — Conectando brasileiros nos EUA
      </td>
    </tr>
  </table>
</body>
</html>"""
