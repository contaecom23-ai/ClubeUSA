# ============================================================
#  services/email_service.py — Clube USA
#  Envio de email transacional (SendGrid ou log em dev)
# ============================================================
import os
import logging
import secrets
from datetime import datetime, timedelta

log = logging.getLogger("email_service")

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@clubeusa.com")
FROM_NAME = os.environ.get("FROM_NAME", "Clube USA")

EMAIL_VERIFICATION_TTL_HRS = 24


def _send_via_sendgrid(to: str, subject: str, html_body: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return False
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=(FROM_EMAIL, FROM_NAME),
            to_emails=to,
            subject=subject,
            html_content=html_body,
        )
        response = sg.send(message)
        log.info(f"Email enviado via SendGrid para {to}: status {response.status_code}")
        return response.status_code in (200, 202)
    except ImportError:
        log.warning("sendgrid nao instalado. Adicione 'sendgrid' ao requirements.txt.")
        return False
    except Exception as e:
        log.error(f"SendGrid erro: {e}")
        return False


def send_email(to: str, subject: str, html_body: str) -> bool:
    """
    Envia email transacional.
    Em producao usa SendGrid (SENDGRID_API_KEY env var).
    Em dev, loga o conteudo.
    """
    if os.environ.get("SENDGRID_API_KEY"):
        return _send_via_sendgrid(to, subject, html_body)

    # Dev / fallback: loga link para facil teste manual
    log.info(f"[DEV EMAIL] Para: {to}")
    log.info(f"[DEV EMAIL] Assunto: {subject}")
    # Extrai o link do body para facilitar testes
    import re
    links = re.findall(r'href="([^"]+)"', html_body)
    for link in links:
        log.info(f"[DEV EMAIL] Link: {link}")
    return True


# ============================================================
#  TEMPLATES
# ============================================================

def send_verification_email(to: str, token: str, name: str = "") -> bool:
    """Envia email de confirmacao com link unico."""
    verify_url = f"{APP_URL}/auth/email/verify?token={token}"
    greeting = f"Olá{', ' + name if name else ''}!"
    subject = "Confirme seu email — Clube USA"
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f0e8;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f0e8;padding:40px 0">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:12px;overflow:hidden;max-width:600px">
      <tr><td style="background:#0D1B3E;padding:28px 32px">
        <h1 style="margin:0;color:#fff;font-size:24px;font-weight:800">Clube USA</h1>
        <p style="margin:4px 0 0;color:rgba(255,255,255,.6);font-size:13px">O maior clube de ofertas para latinos nos EUA</p>
      </td></tr>
      <tr><td style="padding:36px 32px">
        <h2 style="color:#0D1B3E;margin:0 0 12px;font-size:20px">Confirme seu email</h2>
        <p style="color:#374151;line-height:1.6;margin:0 0 28px">{greeting} Clique no botão abaixo para confirmar seu endereço de email e ativar todos os recursos da sua conta.</p>
        <a href="{verify_url}" style="display:inline-block;background:#B0202F;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">✓ Confirmar Email</a>
        <p style="color:#6B7280;font-size:13px;margin:28px 0 0;line-height:1.5">
          Este link expira em 24 horas.<br>
          Se você não criou uma conta no Clube USA, ignore este email.<br><br>
          Ou copie e cole este link no navegador:<br>
          <a href="{verify_url}" style="color:#B0202F;word-break:break-all">{verify_url}</a>
        </p>
      </td></tr>
      <tr><td style="background:#f9fafb;padding:20px 32px;border-top:1px solid #e5e7eb">
        <p style="color:#9ca3af;font-size:12px;margin:0">© 2026 Clube USA · <a href="https://clubeusa.com" style="color:#9ca3af">clubeusa.com</a></p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""
    return send_email(to, subject, html)


def generate_verification_token() -> str:
    """Gera token seguro para verificacao de email (48 bytes = 64 chars hex)."""
    return secrets.token_hex(48)


def verification_expires_at() -> str:
    """Retorna ISO timestamp de expiracao (24h)."""
    return (datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_TTL_HRS)).isoformat()
