import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import get_settings


def _confirmation_html(full_name: str, confirm_url: str) -> str:
    return f"""
<html><body style="font-family:sans-serif;max-width:600px;margin:0 auto">
<h2 style="color:#1a56db">Bem-vindo ao Clube USA, {full_name}!</h2>
<p>Confirme seu e-mail clicando no botão abaixo:</p>
<p>
  <a href="{confirm_url}"
     style="background:#1a56db;color:#fff;padding:12px 24px;
            border-radius:6px;text-decoration:none;display:inline-block">
    Confirmar e-mail
  </a>
</p>
<p style="color:#6b7280;font-size:14px">
  O link expira em 24 horas.<br>
  Se você não criou uma conta, ignore este e-mail.
</p>
</body></html>
"""


def send_confirmation_email(email: str, full_name: str, token: str) -> None:
    s = get_settings()
    confirm_url = f"{s.app_url}/confirm-email.html?token={token}"

    if not s.smtp_host:
        # Development: print to stdout so the tester can copy the link
        print(
            f"\n[EMAIL — console fallback]\nTo: {email}\nSubject: Confirme seu e-mail — Clube USA\nLink: {confirm_url}\n"
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu e-mail — Clube USA"
    msg["From"] = f"{s.email_from_name} <{s.email_from}>"
    msg["To"] = email
    msg.attach(MIMEText(_confirmation_html(full_name, confirm_url), "html"))

    ctx = ssl.create_default_context()
    with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
        server.starttls(context=ctx)
        if s.smtp_user:
            server.login(s.smtp_user, s.smtp_password)
        server.sendmail(s.email_from, [email], msg.as_string())
