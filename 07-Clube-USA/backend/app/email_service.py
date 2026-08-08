"""
Abstração de envio de email.
Troca o provedor via EMAIL_PROVIDER no .env sem mudar o restante do código.
Provedores suportados: console (dev) | sendgrid | resend
"""
import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_email(to: str, subject: str, html_body: str) -> None:
    s = get_settings()
    provider = s.email_provider.lower()

    if provider == "console":
        _send_console(to, subject, html_body)
    elif provider == "sendgrid":
        await _send_sendgrid(to, subject, html_body)
    elif provider == "resend":
        await _send_resend(to, subject, html_body)
    else:
        logger.error("EMAIL_PROVIDER '%s' desconhecido; email não enviado.", provider)


def _send_console(to: str, subject: str, html_body: str) -> None:
    logger.info("=== [EMAIL CONSOLE] ===")
    logger.info("Para: %s", to)
    logger.info("Assunto: %s", subject)
    logger.info("Corpo:\n%s", html_body)
    logger.info("=== [FIM EMAIL] ===")


async def _send_sendgrid(to: str, subject: str, html_body: str) -> None:
    s = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {s.email_api_key}"},
            json={
                "personalizations": [{"to": [{"email": to}]}],
                "from": {"email": s.email_from},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_body}],
            },
            timeout=10,
        )
        if resp.status_code not in (200, 202):
            logger.error("Sendgrid erro %s: %s", resp.status_code, resp.text)


async def _send_resend(to: str, subject: str, html_body: str) -> None:
    s = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {s.email_api_key}"},
            json={"from": s.email_from, "to": [to], "subject": subject, "html": html_body},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.error("Resend erro %s: %s", resp.status_code, resp.text)


def build_confirmation_email(full_name: str, confirm_url: str) -> tuple[str, str]:
    subject = "Confirme seu email — Clube USA"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#1a56db">Bem-vindo ao Clube USA, {full_name}!</h2>
      <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
      <a href="{confirm_url}"
         style="display:inline-block;padding:12px 24px;background:#1a56db;
                color:#fff;text-decoration:none;border-radius:6px;font-weight:bold">
        Confirmar Email
      </a>
      <p style="color:#666;font-size:13px;margin-top:24px">
        Este link expira em 24 horas. Se você não criou uma conta, ignore este email.
      </p>
    </div>
    """
    return subject, html
