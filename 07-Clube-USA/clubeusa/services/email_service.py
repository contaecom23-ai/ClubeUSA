# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais via Resend (preferido) ou SMTP
#
#  Configurar via env vars:
#    EMAIL_PROVIDER=resend   -> usa Resend API (recomendado para produção)
#    EMAIL_PROVIDER=smtp     -> usa SMTP genérico
#    EMAIL_FROM=noreply@clubeusa.com
#    RESEND_API_KEY=re_...
#    SMTP_HOST=smtp.example.com  SMTP_PORT=587
#    SMTP_USER=...  SMTP_PASSWORD=...
# ============================================================

import os
import logging
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_service")

_EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def _hash_token(token: str) -> str:
    """SHA-256 do token — armazena apenas o hash, nunca o token em texto puro."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_confirmation_token(member_id: str) -> str:
    """
    Gera token criptograficamente aleatório, salva hash no banco com TTL 24h.
    Invalida tokens anteriores do mesmo membro.
    Retorna o token em texto puro (para incluir no link do email).
    """
    from supabase import create_client

    token = secrets.token_urlsafe(32)
    token_hash = _hash_token(token)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()

    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    # Invalida tokens anteriores (single-use per member)
    sb.table("email_confirmation_tokens").delete().eq("member_id", member_id).is_("used_at", "null").execute()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token_hash": token_hash,
        "expires_at": expires_at,
    }).execute()

    return token


def verify_confirmation_token(token: str) -> str | None:
    """
    Verifica token de confirmação.
    Retorna member_id se válido, None caso contrário.
    Marca como usado (single-use) ao verificar.
    """
    from supabase import create_client

    token_hash = _hash_token(token)
    sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])

    result = sb.table("email_confirmation_tokens").select(
        "id,member_id,expires_at,used_at"
    ).eq("token_hash", token_hash).execute()

    if not result.data:
        return None

    record = result.data[0]

    if record.get("used_at"):
        return None  # já usado

    expires = datetime.fromisoformat(record["expires_at"].replace("Z", "+00:00"))
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) > expires:
        return None  # expirado

    # Marca como usado (single-use)
    sb.table("email_confirmation_tokens").update({
        "used_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", record["id"]).execute()

    return record["member_id"]


def send_confirmation_email(email: str, token: str, language: str = "pt") -> bool:
    """
    Envia email de confirmação.
    Retorna True se enviado, False se falhou.
    Em desenvolvimento (sem chave configurada), apenas loga o link.
    """
    confirm_url = f"{_APP_URL}/auth/email/confirm/{token}"

    subjects = {
        "pt": "Confirme seu email — Clube USA",
        "es": "Confirma tu correo — Club USA",
    }
    bodies_html = {
        "pt": f"""
<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
  <h2 style="color:#1a56db">Clube USA</h2>
  <p>Olá! Clique no botão abaixo para confirmar seu email e liberar todos os recursos da plataforma.</p>
  <a href="{confirm_url}"
     style="display:inline-block;background:#1a56db;color:#fff;padding:12px 28px;
            border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
    Confirmar meu email
  </a>
  <p style="color:#6b7280;font-size:13px">
    Link válido por 24 horas.<br>
    Se você não criou uma conta no Clube USA, ignore este email.
  </p>
  <p style="color:#6b7280;font-size:12px">
    Ou copie este link no navegador:<br>
    <a href="{confirm_url}" style="color:#1a56db">{confirm_url}</a>
  </p>
</div>""",
        "es": f"""
<div style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:32px 24px">
  <h2 style="color:#1a56db">Club USA</h2>
  <p>¡Hola! Haz clic en el botón para confirmar tu correo y desbloquear todos los recursos.</p>
  <a href="{confirm_url}"
     style="display:inline-block;background:#1a56db;color:#fff;padding:12px 28px;
            border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
    Confirmar mi correo
  </a>
  <p style="color:#6b7280;font-size:13px">
    Enlace válido por 24 horas.<br>
    Si no creaste una cuenta en Club USA, ignora este correo.
  </p>
  <p style="color:#6b7280;font-size:12px">
    O copia este enlace en tu navegador:<br>
    <a href="{confirm_url}" style="color:#1a56db">{confirm_url}</a>
  </p>
</div>""",
    }

    subject = subjects.get(language, subjects["pt"])
    body_html = bodies_html.get(language, bodies_html["pt"])

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()

    if provider == "resend":
        return _send_via_resend(email, subject, body_html)
    elif provider == "smtp":
        return _send_via_smtp(email, subject, body_html)
    else:
        # Dev/sem config: loga o link (não envia email real)
        log.info(f"[DEV] Email de confirmação para {email}: {confirm_url}")
        return True


def _send_via_resend(to: str, subject: str, html: str) -> bool:
    """Envia via Resend API (resend.com — free tier: 3k emails/mês)."""
    import requests as req

    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        log.error("RESEND_API_KEY não configurada.")
        return False

    try:
        resp = req.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": _EMAIL_FROM, "to": [to], "subject": subject, "html": html},
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return True
        log.error(f"Resend erro {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Falha ao enviar email via Resend: {e}")
        return False


def _send_via_smtp(to: str, subject: str, html: str) -> bool:
    """Envia via SMTP (Gmail, Mailgun SMTP, etc.)."""
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER", "")
    password = os.environ.get("SMTP_PASSWORD", "")

    if not all([host, user, password]):
        log.error("Configuração SMTP incompleta.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = _EMAIL_FROM
        msg["To"] = to
        msg.attach(MIMEText(html, "html", "utf-8"))

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(_EMAIL_FROM, [to], msg.as_string())

        return True
    except Exception as e:
        log.error(f"Falha ao enviar email via SMTP: {e}")
        return False
