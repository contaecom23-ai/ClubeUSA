# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais via SMTP
#
#  Vars de ambiente necessarias (producao):
#    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASS, EMAIL_FROM
#  Em dev (ENVIRONMENT != "production") apenas loga o link — sem envio real.
# ============================================================

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")


def send_email_confirmation(
    to_email: str,
    member_name: str,
    confirm_url: str,
    language: str = "pt",
) -> None:
    """Envia email de confirmacao de endereco de email."""
    if os.environ.get("ENVIRONMENT") != "production":
        log.info(f"[DEV] Email confirm → {to_email} | url: {confirm_url}")
        return

    subject = (
        "Confirme seu email — Clube USA"
        if language == "pt"
        else "Confirma tu email — Club USA"
    )
    body = _build_body(member_name, confirm_url, language)
    _send_smtp(to_email, subject, body)


def _build_body(name: str, confirm_url: str, language: str) -> str:
    greeting = f"Olá{', ' + name if name else ''}" if language == "pt" else f"¡Hola{', ' + name if name else ''}"
    if language == "pt":
        return (
            f"{greeting}!\n\n"
            f"Clique no link abaixo para confirmar seu email no Clube USA:\n\n"
            f"{confirm_url}\n\n"
            f"O link expira em 24 horas.\n"
            f"Se você não fez esse pedido, ignore este email.\n\n"
            f"— Clube USA"
        )
    return (
        f"{greeting}!\n\n"
        f"Haz clic en el enlace para confirmar tu email en Club USA:\n\n"
        f"{confirm_url}\n\n"
        f"El enlace expira en 24 horas.\n"
        f"Si no realizaste esta solicitud, ignora este email.\n\n"
        f"— Club USA"
    )


def _send_smtp(to: str, subject: str, body: str) -> None:
    host  = os.environ.get("SMTP_HOST", "")
    port  = int(os.environ.get("SMTP_PORT", "587"))
    user  = os.environ.get("SMTP_USER", "")
    pwd   = os.environ.get("SMTP_PASS", "")
    from_ = os.environ.get("EMAIL_FROM", user)

    if not host or not user:
        log.error("SMTP nao configurado (SMTP_HOST/SMTP_USER ausentes) — email nao enviado.")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"Clube USA <{from_}>"
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, pwd)
            smtp.sendmail(from_, to, msg.as_string())
        log.info(f"Email enviado para {to[:3]}***")
    except Exception as exc:
        log.error(f"Falha SMTP ao enviar para {to[:3]}***: {exc}")
