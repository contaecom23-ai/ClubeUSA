import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    settings = get_settings()
    confirm_url = f"{settings.BASE_URL}/auth/confirm/{token}"

    if not settings.SMTP_HOST:
        # Sem SMTP em dev: loga o link sem expor o email completo
        logger.warning(
            "SMTP não configurado. Link de confirmação para %s***: %s",
            to_email[:3],
            confirm_url,
        )
        return

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; color: #222;">
      <h2 style="color: #1a56db;">Bem-vindo ao Clube USA, {full_name}!</h2>
      <p>Obrigado por se cadastrar. Clique no botão abaixo para confirmar seu email:</p>
      <p style="text-align: center; margin: 32px 0;">
        <a href="{confirm_url}"
           style="background:#1a56db;color:#fff;padding:14px 28px;border-radius:6px;
                  text-decoration:none;font-weight:bold;">
          Confirmar meu email
        </a>
      </p>
      <p style="color:#666;font-size:13px;">O link expira em 24 horas.<br>
      Se você não se cadastrou no Clube USA, ignore este email.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    await aiosmtplib.send(
        msg,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER or None,
        password=settings.SMTP_PASSWORD or None,
        use_tls=settings.SMTP_PORT == 465,
        start_tls=settings.SMTP_PORT == 587,
    )
