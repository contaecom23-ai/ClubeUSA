import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, html: str) -> bool:
    s = get_settings()
    if not s.smtp_user or not s.smtp_password:
        logger.warning("SMTP not configured — email to %s skipped", to)
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = s.smtp_from
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=10) as conn:
            conn.starttls()
            conn.login(s.smtp_user, s.smtp_password)
            conn.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email to %s", to)
        return False


def send_confirmation_email(to: str, token: str, full_name: str) -> bool:
    s = get_settings()
    confirm_url = f"{s.frontend_url}/confirm-email.html?token={token}"
    html = f"""
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:24px;color:#111">
  <h2 style="color:#1e40af">Bem-vindo ao Clube USA!</h2>
  <p>Ola, {full_name}!</p>
  <p>Confirme seu email clicando no botao abaixo para ativar sua conta:</p>
  <p style="text-align:center;margin:32px 0">
    <a href="{confirm_url}"
       style="background:#1e40af;color:#fff;padding:14px 28px;text-decoration:none;border-radius:8px;font-size:16px">
      Confirmar email
    </a>
  </p>
  <p style="color:#6b7280;font-size:13px">
    Este link expira em 24 horas.<br>
    Se voce nao criou esta conta, ignore este email.
  </p>
  <p style="font-size:13px">Link direto: <a href="{confirm_url}">{confirm_url}</a></p>
  <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0">
  <p style="color:#9ca3af;font-size:12px">Clube USA — Sua comunidade brasileira nos EUA</p>
</body>
</html>"""
    return send_email(to, "Confirme seu email — Clube USA", html)
