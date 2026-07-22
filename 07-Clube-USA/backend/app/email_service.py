"""
Serviço de email.
Se SMTP_HOST não estiver configurado, imprime no log (modo dev).
Em produção, configure as variáveis SMTP_* para um provedor real.
"""
import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to_email: str, subject: str, html_body: str) -> None:
    if not settings.SMTP_HOST:
        logger.info("EMAIL (modo dev) | Para: %s | Assunto: %s", to_email, subject)
        logger.info("EMAIL BODY:\n%s", html_body)
        return

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to_email, subject, html_body)


def _send_sync(to_email: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())


# ── Templates ────────────────────────────────────────────────────────────

async def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.FRONTEND_URL}/confirm-email.html?token={token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
      <h2 style="color: #1e40af;">Bem-vindo(a) ao Clube USA, {full_name}!</h2>
      <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
      <p style="text-align: center; margin: 32px 0;">
        <a href="{confirm_url}"
           style="background: #1e40af; color: white; padding: 14px 28px;
                  border-radius: 8px; text-decoration: none; font-weight: bold;">
          Confirmar Email
        </a>
      </p>
      <p style="color: #6b7280; font-size: 13px;">
        Este link expira em 24 horas.<br>
        Se você não criou uma conta, ignore este email.
      </p>
    </div>
    """
    await send_email(to_email, "Confirme seu email — Clube USA", html)
