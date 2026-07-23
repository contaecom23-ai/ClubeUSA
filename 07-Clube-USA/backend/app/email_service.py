import asyncio
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from .config import get_settings


def _send_sync(to_email: str, subject: str, html: str) -> None:
    s = get_settings()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{s.EMAIL_FROM_NAME} <{s.EMAIL_FROM}>"
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT) as srv:
        srv.ehlo()
        srv.starttls(context=ctx)
        srv.login(s.SMTP_USER, s.SMTP_PASS)
        srv.send_message(msg)


async def send_email(to_email: str, subject: str, html: str) -> None:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, to_email, subject, html)


async def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    s = get_settings()
    confirm_url = f"{s.APP_URL}/confirm-email.html?token={token}"

    if not s.SMTP_HOST:
        print(f"[DEV] Confirmation link for {to_email}: {confirm_url}", flush=True)
        return

    first_name = full_name.split()[0] if full_name else "amigo(a)"
    html = f"""
<!DOCTYPE html>
<html lang="pt-BR"><body style="font-family:sans-serif;max-width:560px;margin:auto;padding:24px">
  <h2 style="color:#1a56db">Bem-vindo(a) ao Clube USA, {first_name}!</h2>
  <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
  <a href="{confirm_url}" style="display:inline-block;background:#1a56db;color:#fff;
     text-decoration:none;padding:12px 24px;border-radius:6px;font-weight:bold">
    Confirmar meu email
  </a>
  <p style="color:#6b7280;font-size:14px;margin-top:24px">
    Este link expira em 24 horas.<br>
    Se você não se cadastrou no Clube USA, ignore este email.
  </p>
</body></html>
"""
    await send_email(to_email, "Confirme seu email — Clube USA", html)
