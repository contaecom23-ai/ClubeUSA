"""
Serviço de e-mail com SMTP assíncrono.
Em DEBUG=True, loga o link no console em vez de enviar (dev sem credenciais).
"""
import logging

import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> None:
    if settings.DEBUG or not settings.SMTP_HOST:
        logger.info(
            "[DEV - EMAIL NÃO ENVIADO] Para: %s | Assunto: %s\n%s",
            to, subject, html_body,
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


async def send_confirmation_email(to: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.APP_URL}/confirm-email.html?token={token}"
    subject = "Confirme seu e-mail — Clube USA"
    html_body = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:auto">
      <h2>Bem-vindo(a) ao Clube USA, {full_name}!</h2>
      <p>Clique no botão abaixo para confirmar seu e-mail e ativar sua conta:</p>
      <p style="text-align:center">
        <a href="{confirm_url}"
           style="background:#1a73e8;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;font-size:16px">
          Confirmar E-mail
        </a>
      </p>
      <p style="color:#666;font-size:13px">
        Link válido por 24 horas. Se você não criou uma conta, ignore este e-mail.
      </p>
      <p style="color:#999;font-size:12px">
        Ou copie e cole: {confirm_url}
      </p>
    </body></html>
    """
    await send_email(to, subject, html_body)
