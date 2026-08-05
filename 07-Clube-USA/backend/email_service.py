import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


async def send_confirmation_email(to_email: str, first_name: str, token: str) -> None:
    confirm_url = f"{settings.APP_URL}/confirm-email.html?token={token}"
    subject = "Confirme seu email — Clube USA"
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#212529">
      <h2 style="color:#1B4FBB">Olá, {first_name}!</h2>
      <p>Bem-vindo ao <strong>Clube USA</strong>! Para ativar sua conta, confirme seu email:</p>
      <p style="margin:32px 0">
        <a href="{confirm_url}"
           style="background:#1B4FBB;color:#fff;padding:14px 28px;text-decoration:none;border-radius:6px;font-size:16px">
          Confirmar Email
        </a>
      </p>
      <p style="color:#6c757d;font-size:14px">Este link expira em <strong>24 horas</strong>.</p>
      <p style="color:#6c757d;font-size:14px">Se você não criou uma conta no Clube USA, ignore este email.</p>
      <hr style="border:none;border-top:1px solid #dee2e6;margin:32px 0">
      <p style="color:#adb5bd;font-size:12px">Clube USA — suporte para imigrantes brasileiros nos EUA</p>
    </body>
    </html>
    """

    if not settings.SMTP_HOST:
        logger.info("[EMAIL CONSOLE] Para: %s | Assunto: %s", to_email, subject)
        logger.info("[EMAIL CONSOLE] Link de confirmação: %s", confirm_url)
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.EMAIL_FROM, to_email, msg.as_string())

        logger.info("Email de confirmação enviado para %s", to_email)
    except Exception:
        # Não falha o cadastro por falha de email — loga e segue.
        logger.exception("Falha ao enviar email de confirmação para %s", to_email)
