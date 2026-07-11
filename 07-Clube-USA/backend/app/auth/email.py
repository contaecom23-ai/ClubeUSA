"""
Email sending abstraction.

Default provider: "log" — prints to stdout, no external dependency.
Production provider: "smtp" — configure via SMTP_* env vars.

To add SendGrid / Resend / SES, add a new class and register it in _get_sender().
The owner decides which provider to use (see DECISOES.md).
"""
import smtplib
import sys
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from functools import lru_cache

from app.config import get_settings


class EmailSender(ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None: ...


class LogEmailSender(EmailSender):
    """Dev-mode: logs email content to stdout instead of sending."""
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        print(
            f"\n{'─'*60}\n[EMAIL — LOG MODE] To: {to}\nSubject: {subject}\n{text_body}\n{'─'*60}",
            file=sys.stdout,
            flush=True,
        )


class SmtpEmailSender(EmailSender):
    def send(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        s = get_settings()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{s.email_from_name} <{s.email_from_address}>"
        msg["To"] = to
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(s.smtp_host, s.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(s.smtp_user, s.smtp_password)
            server.sendmail(s.email_from_address, to, msg.as_string())


@lru_cache(maxsize=1)
def _get_sender() -> EmailSender:
    provider = get_settings().email_provider.lower()
    if provider == "smtp":
        return SmtpEmailSender()
    return LogEmailSender()


def send_verification_email(to_email: str, user_name: str, token: str) -> None:
    s = get_settings()
    verify_url = f"{s.app_base_url}/verify-email?token={token}"

    text_body = (
        f"Olá, {user_name}!\n\n"
        f"Confirme seu email clicando no link abaixo:\n{verify_url}\n\n"
        "Este link expira em 24 horas.\n\n"
        "Se você não criou uma conta no Clube USA, ignore este email.\n"
    )
    html_body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<body style="font-family:sans-serif;max-width:520px;margin:auto;padding:24px">
  <h2 style="color:#1a56db">Clube USA — Confirme seu email</h2>
  <p>Olá, <strong>{user_name}</strong>!</p>
  <p>Clique no botão abaixo para confirmar seu endereço de email:</p>
  <p style="text-align:center;margin:32px 0">
    <a href="{verify_url}"
       style="background:#1a56db;color:#fff;padding:14px 28px;border-radius:6px;
              text-decoration:none;font-weight:bold;display:inline-block">
      Confirmar Email
    </a>
  </p>
  <p style="color:#666;font-size:13px">
    Ou copie este link: <br>
    <a href="{verify_url}" style="color:#1a56db">{verify_url}</a>
  </p>
  <p style="color:#999;font-size:12px">
    Este link expira em 24 horas.<br>
    Se você não criou uma conta no Clube USA, ignore este email.
  </p>
</body>
</html>
"""
    _get_sender().send(to_email, "Confirme seu email — Clube USA", html_body, text_body)
