"""
Interface de envio de email.

Backends disponíveis:
  console  — imprime no terminal (desenvolvimento; não envia nada real)
  resend   — usa Resend.com API (produção)

Para adicionar outro provedor: implemente a função send() e adicione ao dispatch.
Decisão do provedor: ver DECISOES.md.
"""
import sys

import httpx

from .config import settings


async def send_confirmation_email(email: str, full_name: str, token: str) -> None:
    confirm_url = f"{settings.FRONTEND_URL}/confirm-email.html?token={token}"
    subject = "Confirme seu email — Clube USA"
    body_html = f"""
<p>Olá, {full_name}!</p>
<p>Clique no link abaixo para confirmar seu email e ativar sua conta no Clube USA:</p>
<p><a href="{confirm_url}">{confirm_url}</a></p>
<p>O link expira em 24 horas.</p>
<p>Se você não criou uma conta, ignore este email.</p>
"""
    body_text = (
        f"Olá, {full_name}!\n\n"
        f"Confirme seu email acessando:\n{confirm_url}\n\n"
        f"O link expira em 24 horas."
    )

    backend = settings.EMAIL_BACKEND

    if backend == "console":
        print(
            f"\n[EMAIL - console]\n"
            f"  Para: {email}\n"
            f"  Assunto: {subject}\n"
            f"  URL de confirmação: {confirm_url}\n",
            file=sys.stderr,
        )

    elif backend == "resend":
        await _send_resend(email, subject, body_html, body_text)

    else:
        print(f"[EMAIL] Backend desconhecido '{backend}'. Email NÃO enviado para {email}.", file=sys.stderr)


async def _send_resend(to: str, subject: str, html: str, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
            json={
                "from": settings.EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
                "text": text,
            },
        )
    if resp.status_code not in (200, 201):
        print(f"[EMAIL] Falha ao enviar via Resend: {resp.status_code} {resp.text}", file=sys.stderr)
