"""
Email service — adapter pattern.
EMAIL_SERVICE env var selects the driver:
  "log"      → prints to stdout (development/test, no external dependency)
  "resend"   → Resend API (https://resend.com) — requires RESEND_API_KEY
  "sendgrid" → SendGrid — requires SENDGRID_API_KEY

To add a new provider: implement _send_via_xxx(to, subject, html) and add the branch.
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def send_confirmation_email(to_email: str, full_name: str, token: str) -> None:
    confirm_url = (
        f"{settings.FRONTEND_URL}/confirm_email.html"
        f"?token={token}"
    )
    subject = "Confirme seu email — Clube USA"
    html = f"""
<p>Olá, {full_name}!</p>
<p>Bem-vindo ao <strong>Clube USA</strong>.</p>
<p>Clique no link abaixo para confirmar seu email:</p>
<p><a href="{confirm_url}">{confirm_url}</a></p>
<p>O link expira em 24 horas.</p>
<p>Se você não criou uma conta, ignore este email.</p>
"""
    _dispatch(to_email, subject, html)


def _dispatch(to: str, subject: str, html: str) -> None:
    driver = settings.EMAIL_SERVICE.lower()
    if driver == "log":
        _send_via_log(to, subject, html)
    elif driver == "resend":
        _send_via_resend(to, subject, html)
    elif driver == "sendgrid":
        _send_via_sendgrid(to, subject, html)
    else:
        logger.warning("EMAIL_SERVICE='%s' not recognized — falling back to log.", driver)
        _send_via_log(to, subject, html)


def _send_via_log(to: str, subject: str, html: str) -> None:
    logger.info(
        "[EMAIL LOG] To=%s | Subject=%s | Body (truncated)=%s",
        to, subject, html[:200],
    )
    print(f"\n{'='*60}\n[DEV EMAIL] To: {to}\nSubject: {subject}\n{html}\n{'='*60}\n")


def _send_via_resend(to: str, subject: str, html: str) -> None:
    if not settings.RESEND_API_KEY:
        raise RuntimeError("RESEND_API_KEY not set.")
    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
        json={"from": settings.FROM_EMAIL, "to": [to], "subject": subject, "html": html},
        timeout=10,
    )
    resp.raise_for_status()


def _send_via_sendgrid(to: str, subject: str, html: str) -> None:
    if not settings.SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY not set.")
    resp = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {settings.SENDGRID_API_KEY}"},
        json={
            "personalizations": [{"to": [{"email": to}]}],
            "from": {"email": settings.FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/html", "value": html}],
        },
        timeout=10,
    )
    resp.raise_for_status()
