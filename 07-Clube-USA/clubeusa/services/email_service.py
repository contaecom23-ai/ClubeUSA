# ============================================================
#  services/email_service.py — Clube USA
#  Abstração de envio de email (confirmação + notificações)
#
#  Hierarquia de provedores em produção:
#    1. RESEND_API_KEY  → Resend REST API (sem SDK externo)
#    2. SMTP_HOST       → SMTP genérico (Gmail, SES, Mailgun, etc.)
#    3. (nenhum)        → warning no log; link não enviado
#
#  Em dev/test: loga o link, não bloqueia o fluxo.
# ============================================================

import os
import hashlib
import logging
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")

_UTC = timezone.utc
_TOKEN_TTL_HRS = 24

_SUBJECT = {
    "pt": "Confirme seu email — Clube USA",
    "es": "Confirma tu correo — Club USA",
}

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<body style="font-family:sans-serif;max-width:520px;margin:40px auto;padding:0 20px">
  <h2 style="color:#1a73e8">{title}</h2>
  <p>{intro}</p>
  <p style="margin:32px 0">
    <a href="{url}"
       style="background:#1a73e8;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-weight:bold">
      {btn}
    </a>
  </p>
  <p style="color:#888;font-size:13px">{expiry}</p>
  <p style="color:#bbb;font-size:12px">{ignore}</p>
  <hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>
  <small style="color:#aaa">Clube USA — comunidade para brasileiros nos EUA</small>
</body>
</html>
"""

_COPY = {
    "pt": {
        "title":  "Confirme seu email no Clube USA",
        "intro":  "Clique no botão abaixo para confirmar seu endereço de email:",
        "btn":    "Confirmar Email",
        "expiry": f"Este link expira em {_TOKEN_TTL_HRS} horas.",
        "ignore": "Se você não solicitou esta confirmação, pode ignorar este email.",
    },
    "es": {
        "title":  "Confirma tu correo en Club USA",
        "intro":  "Haz clic en el botón para confirmar tu dirección de correo:",
        "btn":    "Confirmar Correo",
        "expiry": f"Este enlace expira en {_TOKEN_TTL_HRS} horas.",
        "ignore": "Si no solicitaste esto, puedes ignorar este correo.",
    },
}


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _hash_token(token: str) -> str:
    """SHA-256 do token — banco armazena apenas o hash, nunca o token puro."""
    return hashlib.sha256(token.encode()).hexdigest()


# ============================================================
#  Gestão de tokens no banco
# ============================================================

def create_confirmation_token(member_id: str) -> str:
    """
    Gera token seguro, persiste hash no banco e retorna token puro
    (que vai no link do email — nunca armazenado em texto puro).
    Invalida tokens anteriores do mesmo membro antes de criar novo.
    """
    sb = _supabase()
    sb.table("email_confirmation_tokens").delete().eq("member_id", member_id).execute()

    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(_UTC) + timedelta(hours=_TOKEN_TTL_HRS)).isoformat()

    sb.table("email_confirmation_tokens").insert({
        "member_id":  member_id,
        "token_hash": _hash_token(token),
        "expires_at": expires_at,
    }).execute()

    return token


def verify_confirmation_token(token: str) -> str | None:
    """
    Verifica token e retorna member_id se válido; None se inválido/expirado.
    Token é de uso único: deletado após verificação bem-sucedida.
    """
    if not token or len(token) > 200:
        return None

    sb = _supabase()
    result = sb.table("email_confirmation_tokens").select(
        "id,member_id,expires_at"
    ).eq("token_hash", _hash_token(token)).execute()

    if not result.data:
        return None

    row = result.data[0]
    raw_ts = row["expires_at"]
    if raw_ts.endswith("Z"):
        raw_ts = raw_ts[:-1] + "+00:00"
    expires_at = datetime.fromisoformat(raw_ts)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=_UTC)
    if datetime.now(_UTC) > expires_at:
        sb.table("email_confirmation_tokens").delete().eq("id", row["id"]).execute()
        return None

    # Uso único: deleta antes de retornar
    sb.table("email_confirmation_tokens").delete().eq("id", row["id"]).execute()
    return row["member_id"]


# ============================================================
#  Envio de email
# ============================================================

def send_confirmation_email(to_email: str, confirm_url: str, language: str = "pt") -> bool:
    """
    Envia email de confirmação de endereço.
    Retorna True se entregue (ou simulado em dev), False se falhou.
    """
    lang = language if language in _COPY else "pt"
    subject = _SUBJECT[lang]
    copy = _COPY[lang]
    html = _HTML_TEMPLATE.format(url=confirm_url, **copy)

    env = os.environ.get("ENVIRONMENT", "development")
    if env != "production":
        log.info("[DEV] Email confirmation para %s: %s", to_email, confirm_url)
        return True

    resend_key = os.environ.get("RESEND_API_KEY")
    if resend_key:
        return _send_resend(to_email, subject, html, resend_key)

    smtp_host = os.environ.get("SMTP_HOST")
    if smtp_host:
        return _send_smtp(to_email, subject, html)

    log.warning("Nenhum provider de email configurado — link nao enviado para %s", to_email)
    return False


def _send_resend(to_email: str, subject: str, html: str, api_key: str) -> bool:
    import requests
    from_addr = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            json={"from": from_addr, "to": [to_email], "subject": subject, "html": html},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return True
        log.error("Resend erro %s: %.200s", resp.status_code, resp.text)
        return False
    except Exception as exc:
        log.error("Resend falhou: %s", exc)
        return False


def _send_smtp(to_email: str, subject: str, html: str) -> bool:
    from_addr = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    host = os.environ.get("SMTP_HOST", "")
    port = int(os.environ.get("SMTP_PORT", 587))
    user = os.environ.get("SMTP_USER", "")
    pwd  = os.environ.get("SMTP_PASS", os.environ.get("SMTP_PASSWORD", ""))
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"]    = from_addr
        msg["To"]      = to_email
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP(host, port, timeout=10) as srv:
            srv.ehlo()
            srv.starttls()
            if user:
                srv.login(user, pwd)
            srv.sendmail(from_addr, [to_email], msg.as_string())
        return True
    except Exception as exc:
        log.error("SMTP falhou: %s", exc)
        return False
