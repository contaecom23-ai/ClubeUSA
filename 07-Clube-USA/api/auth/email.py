import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import get_settings

logger = logging.getLogger(__name__)


def send_confirmation_email(to_email: str, confirmation_token: str) -> None:
    """Send (or log in dev) the email-confirmation link."""
    settings = get_settings()
    confirm_url = f"{settings.APP_URL}/confirm-email?token={confirmation_token}"

    if not settings.SMTP_HOST:
        # Development: log to console so the flow can be tested without SMTP
        logger.info("[DEV] Confirmation email for %s → %s", to_email, confirm_url)
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    text_body = (
        f"Bem-vindo ao Clube USA!\n\n"
        f"Confirme seu email acessando o link abaixo (válido por 24 horas):\n{confirm_url}\n\n"
        f"Se você não criou uma conta, ignore este email."
    )
    html_body = f"""<!DOCTYPE html>
<html lang="pt-BR"><body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:24px">
  <h2 style="color:#1d4ed8">Bem-vindo ao Clube USA!</h2>
  <p>Confirme seu email clicando no botão abaixo:</p>
  <a href="{confirm_url}"
     style="display:inline-block;background:#1d4ed8;color:#fff;padding:12px 28px;
            border-radius:6px;text-decoration:none;font-weight:bold">
    Confirmar Email
  </a>
  <p style="margin-top:24px;color:#6b7280;font-size:14px">
    O link expira em 24 horas.<br>
    Se você não criou uma conta, ignore este email.
  </p>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as smtp:
            if settings.SMTP_USE_TLS:
                smtp.starttls()
            if settings.SMTP_USER:
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            smtp.sendmail(settings.SMTP_FROM, to_email, msg.as_string())
    except Exception:
        # Email failure must not block registration; user can resend.
        logger.exception("Failed to send confirmation email to %s", to_email)
