import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_verification_email(to_email: str, token: str) -> None:
    """Send email confirmation link.

    Dev mode: if SMTP_HOST is empty, logs the link instead of sending.
    Production: configure SMTP_* vars in .env.
    """
    verify_url = f"{settings.FRONTEND_URL}/verify-email.html?token={token}"

    if not settings.SMTP_HOST:
        # Dev mode — never send real email without SMTP configured
        logger.info("=== [DEV] Email verification link ===")
        logger.info(f"  To: {to_email}")
        logger.info(f"  URL: {verify_url}")
        logger.info("=====================================")
        return

    subject = "Confirme seu email — Clube USA"
    html_body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; padding: 24px;">
  <h2 style="color: #1a56db;">Bem-vindo ao Clube USA!</h2>
  <p>Clique no botão abaixo para confirmar seu endereço de email:</p>
  <a href="{verify_url}"
     style="display:inline-block;background:#1a56db;color:#fff;padding:12px 24px;
            border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0;">
    Confirmar Email
  </a>
  <p style="color:#666;font-size:13px;">
    Este link expira em 24 horas. Se você não criou uma conta, ignore este email.
  </p>
</body>
</html>
"""
    text_body = f"Confirme seu email no Clube USA:\n\n{verify_url}\n\nEste link expira em 24 horas."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        server.ehlo()
        server.starttls()
        if settings.SMTP_USERNAME:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_FROM, [to_email], msg.as_string())
