import asyncio
import logging
import smtplib
import ssl
from concurrent.futures import ThreadPoolExecutor
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)


def _send_sync(to_email: str, subject: str, html: str, text: str) -> None:
    if not settings.SMTP_HOST:
        logger.info("[EMAIL MOCK] To=%s Subject=%s\n%s", to_email, subject, text)
        return

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(text, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls(context=ctx)
        if settings.SMTP_USER:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM, to_email, msg.as_string())


async def _send_async(to_email: str, subject: str, html: str, text: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(_executor, _send_sync, to_email, subject, html, text)


async def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.APP_BASE_URL}/confirm?token={token}"
    subject = "Confirme seu email — Clube USA"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#111;">
  <h2 style="color:#1a56db;">Bem-vindo ao Clube USA, {full_name}!</h2>
  <p>Obrigado por se cadastrar. Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
  <p style="text-align:center;margin:32px 0;">
    <a href="{confirm_url}"
       style="background:#1a56db;color:#fff;padding:14px 28px;text-decoration:none;border-radius:6px;font-size:16px;display:inline-block;">
      Confirmar meu email
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px;">
    Este link expira em <strong>24 horas</strong>.<br>
    Se você não se cadastrou no Clube USA, ignore este email.
  </p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
  <p style="color:#9ca3af;font-size:11px;">Clube USA — A plataforma do imigrante brasileiro nos EUA</p>
</body>
</html>"""

    text = f"""Bem-vindo ao Clube USA, {full_name}!

Confirme seu email acessando o link abaixo:
{confirm_url}

Este link expira em 24 horas.
Se você não se cadastrou no Clube USA, ignore este email.

Clube USA — A plataforma do imigrante brasileiro nos EUA
"""

    try:
        await _send_async(to_email, subject, html, text)
    except Exception:
        logger.exception("Falha ao enviar email de confirmação para %s", to_email)
        # Não propaga: usuário já está no banco, pode usar /auth/resend-confirmation
