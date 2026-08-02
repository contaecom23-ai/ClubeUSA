import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .config import settings

logger = logging.getLogger(__name__)


def _send_smtp(to: str, subject: str, html: str, text: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg["To"] = to
    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_user, settings.smtp_pass)
        server.sendmail(settings.email_from, to, msg.as_string())


def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.app_base_url}/auth/confirm-email?token={token}"

    subject = "Confirme seu email — Clube USA"
    text = (
        f"Olá {full_name},\n\n"
        f"Clique no link abaixo para confirmar seu email:\n{confirm_url}\n\n"
        "O link expira em 24 horas.\n\nClubeUSA"
    )
    html = f"""
    <p>Olá <strong>{full_name}</strong>,</p>
    <p>Clique no botão abaixo para confirmar seu email:</p>
    <p><a href="{confirm_url}" style="background:#2563eb;color:#fff;padding:12px 24px;
       text-decoration:none;border-radius:6px;display:inline-block;">
       Confirmar email
    </a></p>
    <p>Ou cole este link no navegador:<br><small>{confirm_url}</small></p>
    <p>O link expira em 24 horas.</p>
    """

    if settings.is_dev or not settings.smtp_host:
        logger.info("[DEV] Email de confirmação para %s: %s", to_email, confirm_url)
        return

    try:
        _send_smtp(to_email, subject, html, text)
    except Exception as exc:
        # Não vaza detalhes do SMTP em prod; loga internamente
        logger.error("Falha ao enviar email para %s: %s", to_email, exc)
        raise RuntimeError("Erro ao enviar email de confirmação") from exc
