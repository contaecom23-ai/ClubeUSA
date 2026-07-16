import logging

from config import settings

logger = logging.getLogger(__name__)


def send_email_confirmation(to_email: str, name: str, token: str) -> None:
    confirm_url = f"{settings.FRONTEND_URL}/confirm-email.html?token={token}"

    if settings.EMAIL_PROVIDER == "log":
        # Dev mode: nunca loga PII completa em produção
        logger.info("DEV — confirm email for %s: %s", to_email[:3] + "***", confirm_url)
        return

    if settings.EMAIL_PROVIDER == "resend":
        _send_resend(to_email, name, confirm_url)
    elif settings.EMAIL_PROVIDER == "sendgrid":
        _send_sendgrid(to_email, name, confirm_url)
    else:
        raise RuntimeError(f"EMAIL_PROVIDER desconhecido: {settings.EMAIL_PROVIDER!r}")


def _send_resend(to_email: str, name: str, confirm_url: str) -> None:
    import httpx

    r = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.EMAIL_API_KEY}"},
        json={
            "from": settings.EMAIL_FROM,
            "to": [to_email],
            "subject": "Confirme seu email — Clube USA",
            "html": _html(name, confirm_url),
        },
        timeout=10,
    )
    r.raise_for_status()


def _send_sendgrid(to_email: str, name: str, confirm_url: str) -> None:
    import httpx

    r = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {settings.EMAIL_API_KEY}"},
        json={
            "personalizations": [{"to": [{"email": to_email, "name": name}]}],
            "from": {"email": settings.EMAIL_FROM},
            "subject": "Confirme seu email — Clube USA",
            "content": [{"type": "text/html", "value": _html(name, confirm_url)}],
        },
        timeout=10,
    )
    r.raise_for_status()


def _html(name: str, confirm_url: str) -> str:
    safe_name = name.replace("<", "&lt;").replace(">", "&gt;")
    safe_url = confirm_url.replace('"', "%22")
    return f"""
<div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px">
  <h2 style="color:#1a56db">Bem-vindo ao Clube USA, {safe_name}!</h2>
  <p>Clique no botão abaixo para confirmar seu email e ativar sua conta:</p>
  <a href="{safe_url}"
     style="display:inline-block;background:#1a56db;color:white;
            padding:12px 28px;border-radius:6px;text-decoration:none;font-weight:bold">
    Confirmar Email
  </a>
  <p style="color:#888;font-size:12px;margin-top:24px">
    Este link expira em 24 horas.<br>
    Se você não criou uma conta no Clube USA, ignore este email.
  </p>
</div>
"""
