import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import settings

logger = logging.getLogger(__name__)


def _send(to: str, subject: str, html: str) -> bool:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        logger.warning("SMTP não configurado — email NÃO enviado (destinatário omitido dos logs)")
        return False
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.FROM_EMAIL
    msg["To"] = to
    msg.attach(MIMEText(html, "html", "utf-8"))
    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as s:
            s.ehlo()
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASS)
            s.sendmail(settings.FROM_EMAIL, [to], msg.as_bytes())
        return True
    except Exception:
        logger.exception("Falha ao enviar email (destinatário omitido dos logs)")
        return False


def send_confirmation_email(to: str, name: str, token: str) -> bool:
    url = f"{settings.FRONTEND_URL}/confirm.html?token={token}"
    html = f"""
<html><body style="font-family:sans-serif;max-width:600px;margin:auto;padding:20px">
  <h2 style="color:#1a56db">Bem-vindo ao Clube USA, {name}!</h2>
  <p>Clique abaixo para confirmar seu email. O link expira em 24 horas.</p>
  <a href="{url}" style="display:inline-block;background:#1a56db;color:#fff;
     padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold;margin:16px 0">
    Confirmar meu email
  </a>
  <p style="color:#666;font-size:13px">Ou cole este link no navegador:<br>
    <a href="{url}">{url}</a></p>
  <hr style="border:none;border-top:1px solid #eee;margin-top:32px">
  <p style="color:#999;font-size:12px">Clube USA — para imigrantes brasileiros nos EUA</p>
</body></html>"""
    return _send(to, "Confirme seu email — Clube USA", html)
