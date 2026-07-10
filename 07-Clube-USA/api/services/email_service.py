"""
Transactional email via SMTP (compatible with SendGrid, Mailgun, Resend SMTP, SES).
If SMTP_HOST is not configured, emails are logged to stderr (dev mode only).
PII (email addresses) is never logged beyond the warning level.
"""
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from ..config import settings

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_FROM)


def send_confirmation_email(to_email: str, confirm_url: str) -> None:
    subject = "Confirme seu email — Clube USA"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #1a56db;">Bem-vindo ao Clube USA! 🇧🇷🇺🇸</h2>
      <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
      <a href="{confirm_url}"
         style="display:inline-block;background:#1a56db;color:#fff;padding:14px 28px;
                text-decoration:none;border-radius:6px;font-weight:bold;margin:16px 0;">
        Confirmar meu email
      </a>
      <p style="color:#666;font-size:13px;">
        Link válido por 24 horas. Se você não criou uma conta, ignore este email.
      </p>
      <p style="color:#666;font-size:13px;">
        Ou copie e cole este link no navegador:<br>
        <span style="word-break:break-all;">{confirm_url}</span>
      </p>
    </body>
    </html>
    """
    plain = (
        f"Confirme seu email no Clube USA:\n\n{confirm_url}\n\n"
        "Link válido por 24 horas."
    )
    _send(to_email, subject, html, plain)


def send_welcome_email(to_email: str, full_name: str) -> None:
    subject = "Email confirmado — Bem-vindo ao Clube USA!"
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #1a56db;">Email confirmado com sucesso, {full_name}!</h2>
      <p>Sua conta no Clube USA está ativa. Faça login e explore a plataforma.</p>
      <a href="{settings.FRONTEND_URL}/login.html"
         style="display:inline-block;background:#1a56db;color:#fff;padding:14px 28px;
                text-decoration:none;border-radius:6px;font-weight:bold;margin:16px 0;">
        Fazer login
      </a>
    </body>
    </html>
    """
    plain = f"Olá {full_name}, seu email foi confirmado! Acesse: {settings.FRONTEND_URL}/login.html"
    _send(to_email, subject, html, plain)


def _send(to_email: str, subject: str, html: str, plain: str) -> None:
    if not _is_configured():
        logger.warning(
            "[DEV MODE] SMTP not configured — email NOT sent. "
            "Subject: %s | To: [redacted]",
            subject,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email

    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        if settings.SMTP_TLS:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.starttls(context=context)
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
        else:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
                if settings.SMTP_USER:
                    server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(settings.SMTP_FROM, [to_email], msg.as_string())
    except Exception:
        # Do not log the email address in the exception (PII)
        logger.exception("[EMAIL] Failed to send email (subject: %s)", subject)
        raise
