# ============================================================
#  services/email_service.py — Clube USA
#
#  Abstrai o envio de emails. Em dev loga o conteudo.
#  Em producao, wire to an email provider via EMAIL_PROVIDER env var.
#
#  DECISOES.md: dono deve escolher provider (Resend, SendGrid, SES).
# ============================================================

import os
import logging

log = logging.getLogger("email_service")

APP_URL      = os.environ.get("APP_URL", "https://clubeusa.com")
FROM_ADDRESS = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")


def send_email_confirmation(to_email: str, confirm_token_raw: str) -> bool:
    """
    Envia email de confirmacao de endereco.

    Args:
        to_email: email do destinatario (plain text, nao criptografado)
        confirm_token_raw: token raw (nao o hash) para montar o link

    Returns:
        True se enviado (ou logado em dev), False se falhou.
    """
    link = f"{APP_URL}/auth/email/confirm?token={confirm_token_raw}"

    subject = "Confirme seu email — Clube USA"
    body_pt = (
        "Ola!\n\n"
        "Clique no link abaixo para confirmar seu email no Clube USA:\n\n"
        f"{link}\n\n"
        "O link expira em 24 horas.\n\n"
        "Se voce nao se cadastrou no Clube USA, ignore este email.\n\n"
        "— Equipe Clube USA"
    )

    env = os.environ.get("ENVIRONMENT", "development")

    if env != "production":
        # Em dev/staging: loga para facilitar testes sem precisar de provider real
        log.info(
            f"[EMAIL-DEV] Para: {to_email} | Assunto: {subject}\n{body_pt}"
        )
        return True

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()

    if provider == "resend":
        return _send_via_resend(to_email, subject, body_pt)
    elif provider == "sendgrid":
        return _send_via_sendgrid(to_email, subject, body_pt)
    else:
        log.error(
            "EMAIL_PROVIDER nao configurado em producao. "
            "Defina EMAIL_PROVIDER=resend|sendgrid e as credenciais correspondentes."
        )
        return False


def _send_via_resend(to_email: str, subject: str, body: str) -> bool:
    """Envia via Resend (https://resend.com)."""
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        log.error("RESEND_API_KEY nao definida.")
        return False
    try:
        import httpx
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": FROM_ADDRESS, "to": [to_email], "subject": subject, "text": body},
            timeout=10,
        )
        if resp.status_code not in (200, 201):
            log.error(f"Resend retornou {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        log.error(f"Falha ao enviar via Resend: {e}")
        return False


def _send_via_sendgrid(to_email: str, subject: str, body: str) -> bool:
    """Envia via SendGrid."""
    api_key = os.environ.get("SENDGRID_API_KEY", "")
    if not api_key:
        log.error("SENDGRID_API_KEY nao definida.")
        return False
    try:
        import httpx
        resp = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": FROM_ADDRESS},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10,
        )
        if resp.status_code not in (200, 202):
            log.error(f"SendGrid retornou {resp.status_code}: {resp.text[:200]}")
            return False
        return True
    except Exception as e:
        log.error(f"Falha ao enviar via SendGrid: {e}")
        return False
