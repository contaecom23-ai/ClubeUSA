import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)

_CONFIRM_HTML = """\
<html>
<body style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;">
  <h2 style="color:#1d4ed8;">Bem-vindo ao Clube USA, {name}!</h2>
  <p>Obrigado por se cadastrar. Clique no botão abaixo para confirmar seu email:</p>
  <p style="margin:32px 0;">
    <a href="{url}"
       style="background:#2563eb;color:#fff;padding:14px 28px;border-radius:8px;
              text-decoration:none;font-weight:600;display:inline-block;">
      Confirmar meu email
    </a>
  </p>
  <p style="color:#6b7280;font-size:14px;">Este link expira em 24 horas.</p>
  <p style="color:#6b7280;font-size:14px;">
    Se você não criou esta conta, ignore este email com segurança.
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:32px 0;">
  <p style="color:#9ca3af;font-size:12px;">Clube USA — A plataforma do imigrante brasileiro nos EUA</p>
</body>
</html>
"""


async def send_confirmation_email(email: str, name: str, token: str) -> None:
    confirm_url = f"{settings.APP_URL}/auth/confirm-email/{token}"

    if not settings.smtp_configured:
        logger.info("DEV MODE: SMTP não configurado. Link de confirmação: %s", confirm_url)
        print(f"\n{'='*60}")
        print(f"DEV — Confirmar email: {email}")
        print(f"Link: {confirm_url}")
        print(f"{'='*60}\n")
        return

    html_body = _CONFIRM_HTML.format(name=name, url=confirm_url)
    message = MIMEMultipart("alternative")
    message["Subject"] = "Confirme seu cadastro no Clube USA"
    message["From"] = settings.SMTP_FROM_EMAIL
    message["To"] = email
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            start_tls=settings.SMTP_TLS,
        )
    except Exception:
        # Log sem expor senha/conteúdo sensível
        logger.exception("Falha ao enviar email de confirmação para %s", email)
