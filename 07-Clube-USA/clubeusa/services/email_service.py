# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais (confirmacao, alertas, etc.)
#
#  Em producao: configura SMTP via env vars (SMTP_HOST, SMTP_PORT,
#  SMTP_USER, SMTP_PASS). Em dev loga o conteudo.
#  Provedor recomendado: ver DECISOES.md.
# ============================================================

import os
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")

_FROM_NAME  = "Clube USA"
_FROM_EMAIL = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
APP_URL     = os.environ.get("APP_URL", "https://clubeusa.com")


def send_email_confirmation(to_email: str, token: str, language: str = "pt"):
    """
    Envia email com link de confirmacao para o endereco fornecido.
    Em dev (ENVIRONMENT != production) loga o link no lugar de enviar.
    """
    confirm_url = f"{APP_URL}/email/confirm?token={token}"

    subjects = {
        "pt": "Confirme seu email — Clube USA",
        "es": "Confirma tu correo — Club USA",
    }
    bodies_text = {
        "pt": (
            f"Ola!\n\n"
            f"Clique no link abaixo para confirmar seu email no Clube USA:\n\n"
            f"{confirm_url}\n\n"
            f"O link expira em 24 horas.\n\n"
            f"Se voce nao se cadastrou no Clube USA, ignore este email.\n\n"
            f"— Equipe Clube USA"
        ),
        "es": (
            f"Hola!\n\n"
            f"Haz clic en el enlace a continuacion para confirmar tu correo en Club USA:\n\n"
            f"{confirm_url}\n\n"
            f"El enlace expira en 24 horas.\n\n"
            f"Si no te registraste en Club USA, ignora este correo.\n\n"
            f"— Equipo Club USA"
        ),
    }
    bodies_html = {
        "pt": f"""
<html><body style="font-family:sans-serif;max-width:560px;margin:auto;">
  <h2 style="color:#1a56db;">Clube USA</h2>
  <p>Olá! Clique no botão abaixo para confirmar seu email.</p>
  <p style="margin:24px 0;">
    <a href="{confirm_url}"
       style="background:#1a56db;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
      Confirmar email
    </a>
  </p>
  <p style="font-size:12px;color:#6b7280;">O link expira em 24 horas.<br>
  Se você não se cadastrou no Clube USA, ignore este email.</p>
</body></html>""",
        "es": f"""
<html><body style="font-family:sans-serif;max-width:560px;margin:auto;">
  <h2 style="color:#1a56db;">Club USA</h2>
  <p>¡Hola! Haz clic en el botón para confirmar tu correo.</p>
  <p style="margin:24px 0;">
    <a href="{confirm_url}"
       style="background:#1a56db;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;">
      Confirmar correo
    </a>
  </p>
  <p style="font-size:12px;color:#6b7280;">El enlace expira en 24 horas.<br>
  Si no te registraste en Club USA, ignora este correo.</p>
</body></html>""",
    }

    lang = language if language in ("pt", "es") else "pt"
    subject   = subjects[lang]
    body_text = bodies_text[lang]
    body_html = bodies_html[lang]

    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Email confirmacao para {to_email}: {confirm_url}")
        return

    _send_smtp(to_email, subject, body_text, body_html)


def _send_smtp(to_email: str, subject: str, body_text: str, body_html: str):
    """Envia via SMTP. Exige SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS no env."""
    host = os.environ.get("SMTP_HOST")
    port = int(os.environ.get("SMTP_PORT", "587"))
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASS")

    if not all([host, user, password]):
        log.warning("SMTP nao configurado — email nao enviado.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{_FROM_NAME} <{_FROM_EMAIL}>"
    msg["To"]      = to_email

    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(_FROM_EMAIL, to_email, msg.as_string())
        log.info(f"Email enviado para {to_email}")
    except Exception as e:
        log.error(f"Falha ao enviar email para {to_email}: {e}")
        raise
