# ============================================================
#  utils/email.py — Clube USA
#  Envio de emails transacionais (confirmacao, alertas)
#
#  Provedor configuravel via env vars:
#    EMAIL_PROVIDER=sendgrid   -> usa SendGrid v3 REST API
#    EMAIL_FROM=no-reply@clubeusa.com
#    SENDGRID_API_KEY=SG.xxx
#
#  Em desenvolvimento (sem EMAIL_PROVIDER), apenas loga o link.
# ============================================================

import os
import logging
import secrets
from datetime import datetime, timedelta, timezone

log = logging.getLogger("email_util")

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def generate_confirm_token() -> str:
    """Token opaco de 32 bytes, URL-safe."""
    return secrets.token_urlsafe(32)


def send_confirmation_email(to_email: str, name: str, token: str) -> bool:
    """
    Envia email de confirmacao de cadastro.

    Retorna True se enviado (ou logado em dev), False em falha.
    Em dev (sem EMAIL_PROVIDER), apenas loga o link.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm?token={token}"
    name_display = name or "membro"

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()

    if provider == "sendgrid":
        return _send_sendgrid(to_email, name_display, confirm_url)

    # Dev fallback: loga link (evita expor email real em prod sem config)
    log.info(
        f"[DEV] Email de confirmacao para {to_email[:3]}***"
        f" | link: {confirm_url}"
    )
    return True


def _send_sendgrid(to_email: str, name: str, confirm_url: str) -> bool:
    """Chama a SendGrid v3 API via requests (sem dep extra)."""
    import requests

    api_key = os.environ.get("SENDGRID_API_KEY", "")
    from_email = os.environ.get("EMAIL_FROM", "no-reply@clubeusa.com")

    if not api_key:
        log.warning("SENDGRID_API_KEY nao configurada — email nao enviado.")
        return False

    body = {
        "personalizations": [{
            "to": [{"email": to_email, "name": name}],
            "dynamic_template_data": {
                "name": name,
                "confirm_url": confirm_url,
            },
        }],
        "from": {"email": from_email, "name": "Clube USA"},
        "subject": "Confirme seu email — Clube USA",
        "content": [{
            "type": "text/html",
            "value": _html_body(name, confirm_url),
        }],
    }

    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=body,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=10,
        )
        if resp.status_code in (200, 202):
            return True
        log.error(f"SendGrid erro {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Falha ao enviar email via SendGrid: {e}")
        return False


def _html_body(name: str, confirm_url: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Confirme seu email</title></head>
<body style="font-family:Arial,sans-serif;background:#f5f5f5;margin:0;padding:20px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:32px">
    <h2 style="color:#0a1f44;margin:0 0 8px">Clube USA</h2>
    <p style="color:#555;margin:0 0 24px;font-size:15px">
      Olá, {name}! Clique no botão abaixo para confirmar seu email e ativar sua conta.
    </p>
    <a href="{confirm_url}"
       style="display:inline-block;background:#0a1f44;color:#fff;text-decoration:none;
              padding:14px 28px;border-radius:8px;font-weight:700;font-size:15px">
      Confirmar email →
    </a>
    <p style="color:#999;font-size:12px;margin:24px 0 0">
      Link válido por 72 horas. Se não foi você, ignore este email.
    </p>
  </div>
</body>
</html>
"""
