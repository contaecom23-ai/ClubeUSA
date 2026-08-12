import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

_SMTP_HOST = os.environ.get("EMAIL_SMTP_HOST", "")
_SMTP_PORT = int(os.environ.get("EMAIL_SMTP_PORT", "587"))
_SMTP_USER = os.environ.get("EMAIL_SMTP_USER", "")
_SMTP_PASSWORD = os.environ.get("EMAIL_SMTP_PASSWORD", "")
_EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
_APP_URL = os.environ.get("APP_URL", "http://localhost:8000")


def _is_configured() -> bool:
    return bool(_SMTP_HOST and _SMTP_USER and _SMTP_PASSWORD)


def send_confirmation_email(to_email: str, token: str, first_name: str) -> None:
    confirm_url = f"{_APP_URL}/api/auth/confirm-email?token={token}"

    if not _is_configured():
        # Dev mode: log the link so the developer can confirm manually
        logger.warning(
            "[EMAIL NOT SENT — configure EMAIL_SMTP_* env vars] "
            "Confirmation URL for %s: %s",
            to_email,
            confirm_url,
        )
        return

    subject = "Confirme seu email — Clube USA"
    body_text = (
        f"Olá, {first_name}!\n\n"
        "Bem-vindo(a) ao Clube USA. Confirme seu email acessando o link abaixo:\n"
        f"{confirm_url}\n\n"
        "Este link expira em 24 horas.\n\nClube USA"
    )
    body_html = f"""
<html><body style="font-family:sans-serif;max-width:480px;margin:auto">
  <h2>Bem-vindo(a) ao Clube USA, {first_name}!</h2>
  <p>Clique no botão abaixo para confirmar seu email:</p>
  <p>
    <a href="{confirm_url}"
       style="background:#1d4ed8;color:#fff;padding:12px 24px;
              text-decoration:none;border-radius:6px;display:inline-block">
      Confirmar email
    </a>
  </p>
  <p style="color:#6b7280;font-size:0.875rem">
    Link expira em 24 horas. Se você não criou uma conta, ignore este email.
  </p>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = _EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(_SMTP_HOST, _SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(_SMTP_USER, _SMTP_PASSWORD)
            server.sendmail(_EMAIL_FROM, to_email, msg.as_string())
    except Exception:
        # Logged by caller; don't leak SMTP details
        logger.error("Failed to send confirmation email to %s", to_email)
        raise
