"""
Serviço de e-mail plugável.
Backend configurado via EMAIL_BACKEND em .env:
  - "console" : imprime no stdout (dev/teste)
  - "resend"  : usa Resend API (requer RESEND_API_KEY)
  - "sendgrid": usa SendGrid (requer SENDGRID_API_KEY)
"""
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    to: str
    subject: str
    html_body: str
    text_body: str


async def send_email(msg: EmailMessage) -> None:
    from .config import settings

    backend = settings.EMAIL_BACKEND
    if backend == "console":
        await _send_console(msg)
    elif backend == "resend":
        await _send_resend(msg, settings)
    elif backend == "sendgrid":
        await _send_sendgrid(msg, settings)
    else:
        logger.warning("EMAIL_BACKEND desconhecido: %s — e-mail não enviado.", backend)


async def _send_console(msg: EmailMessage) -> None:
    logger.info(
        "\n" + "=" * 60 + "\n[EMAIL CONSOLE]\nPara: %s\nAssunto: %s\n\n%s\n" + "=" * 60,
        msg.to,
        msg.subject,
        msg.text_body,
    )


async def _send_resend(msg: EmailMessage, settings) -> None:
    try:
        import httpx
    except ImportError:
        logger.error("httpx não instalado — necessário para backend Resend.")
        return

    if not settings.RESEND_API_KEY:
        logger.error("RESEND_API_KEY não definida.")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={
                "from": f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>",
                "to": [msg.to],
                "subject": msg.subject,
                "html": msg.html_body,
                "text": msg.text_body,
            },
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            logger.error("Resend retornou %s: %s", resp.status_code, resp.text)


async def _send_sendgrid(msg: EmailMessage, settings) -> None:
    try:
        import httpx
    except ImportError:
        logger.error("httpx não instalado — necessário para backend SendGrid.")
        return

    if not settings.SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY não definida.")
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
            json={
                "personalizations": [{"to": [{"email": msg.to}]}],
                "from": {"email": settings.EMAIL_FROM, "name": settings.EMAIL_FROM_NAME},
                "subject": msg.subject,
                "content": [
                    {"type": "text/plain", "value": msg.text_body},
                    {"type": "text/html", "value": msg.html_body},
                ],
            },
            timeout=10,
        )
        if resp.status_code != 202:
            logger.error("SendGrid retornou %s: %s", resp.status_code, resp.text)


# ──────────────────────────────────────────────
# Templates de e-mail
# ──────────────────────────────────────────────

def build_confirm_email(to: str, full_name: str, confirm_url: str) -> EmailMessage:
    name = full_name or "amigo(a)"
    text = (
        f"Olá {name},\n\n"
        "Confirme seu e-mail clicando no link abaixo:\n\n"
        f"{confirm_url}\n\n"
        "O link expira em 24 horas.\n\n"
        "Bem-vindo(a) ao Clube USA!"
    )
    html = f"""
    <p>Olá <strong>{name}</strong>,</p>
    <p>Confirme seu e-mail clicando no botão abaixo:</p>
    <p>
      <a href="{confirm_url}"
         style="background:#1d4ed8;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;">
        Confirmar e-mail
      </a>
    </p>
    <p>O link expira em 24 horas.</p>
    <p>Bem-vindo(a) ao <strong>Clube USA</strong>!</p>
    """
    return EmailMessage(to=to, subject="Confirme seu e-mail — Clube USA", html_body=html, text_body=text)


def build_password_reset_email(to: str, full_name: str, reset_url: str) -> EmailMessage:
    name = full_name or "usuário(a)"
    text = (
        f"Olá {name},\n\n"
        "Recebemos um pedido de redefinição de senha. Clique no link:\n\n"
        f"{reset_url}\n\n"
        "O link expira em 2 horas. Se não foi você, ignore este e-mail."
    )
    html = f"""
    <p>Olá <strong>{name}</strong>,</p>
    <p>Recebemos um pedido de redefinição de senha:</p>
    <p>
      <a href="{reset_url}"
         style="background:#dc2626;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;">
        Redefinir senha
      </a>
    </p>
    <p>O link expira em 2 horas. Se não foi você, ignore este e-mail.</p>
    """
    return EmailMessage(to=to, subject="Redefinição de senha — Clube USA", html_body=html, text_body=text)
