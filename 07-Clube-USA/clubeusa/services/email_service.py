# ============================================================
#  services/email_service.py — Clube USA
#  Servico de email plugavel (Resend | SendGrid | dev-log)
#
#  Para ativar em producao, configure:
#    EMAIL_PROVIDER=resend        (ou "sendgrid")
#    EMAIL_API_KEY=re_...         (chave da API do provedor)
#    EMAIL_FROM=noreply@clubeusa.com
#
#  Em desenvolvimento (ENVIRONMENT != production) apenas loga a URL —
#  nenhuma dependencia externa necessaria.
# ============================================================

import os
import logging

log = logging.getLogger("email_service")


def send_confirmation_email(to_email: str, confirm_url: str) -> bool:
    """
    Envia email de confirmacao para o usuario.

    - DEV: loga a URL (nenhuma dependencia externa)
    - PROD: usa EMAIL_PROVIDER (resend | sendgrid)

    Retorna True se enviado com sucesso (ou simulado em dev).
    """
    if os.environ.get("ENVIRONMENT", "development") != "production":
        log.info(f"[DEV] Confirmacao de email → {to_email} | URL: {confirm_url}")
        return True

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()
    if provider == "resend":
        return _send_resend(to_email, confirm_url)
    if provider == "sendgrid":
        return _send_sendgrid(to_email, confirm_url)

    log.warning(f"EMAIL_PROVIDER nao configurado — email nao enviado para {to_email}")
    return False


def _send_resend(to_email: str, confirm_url: str) -> bool:
    import requests
    api_key = os.environ.get("EMAIL_API_KEY", "")
    from_addr = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    if not api_key:
        log.error("EMAIL_API_KEY nao configurado para Resend.")
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "from": from_addr,
                "to": [to_email],
                "subject": "Confirme seu email — Clube USA",
                "html": _html(confirm_url),
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info(f"Email enviado via Resend para {to_email}")
        return True
    except Exception as e:
        log.error(f"Resend falhou: {e}")
        return False


def _send_sendgrid(to_email: str, confirm_url: str) -> bool:
    import requests
    api_key = os.environ.get("EMAIL_API_KEY", "")
    from_addr = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
    if not api_key:
        log.error("EMAIL_API_KEY nao configurado para SendGrid.")
        return False
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_addr},
                "subject": "Confirme seu email — Clube USA",
                "content": [{"type": "text/html", "value": _html(confirm_url)}],
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info(f"Email enviado via SendGrid para {to_email}")
        return True
    except Exception as e:
        log.error(f"SendGrid falhou: {e}")
        return False


def _html(confirm_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,Helvetica,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0"
         style="max-width:520px;margin:40px auto;background:#fff;border-radius:8px;
                overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <tr>
      <td style="background:#e63946;padding:28px 32px">
        <h1 style="margin:0;color:#fff;font-size:22px;font-weight:700">Clube USA</h1>
      </td>
    </tr>
    <tr>
      <td style="padding:32px">
        <h2 style="margin:0 0 16px;color:#1a1a2e;font-size:18px">Confirme seu email</h2>
        <p style="color:#444;line-height:1.6;margin:0 0 24px">
          Clique no botao abaixo para confirmar seu endereco de email e
          completar seu cadastro no Clube USA.
        </p>
        <a href="{confirm_url}"
           style="display:inline-block;background:#e63946;color:#fff;padding:14px 28px;
                  border-radius:6px;text-decoration:none;font-weight:700;font-size:15px">
          Confirmar email
        </a>
        <p style="color:#999;font-size:12px;margin:24px 0 0;line-height:1.5">
          Este link expira em 24 horas.<br>
          Se voce nao criou uma conta no Clube USA, ignore este email.
        </p>
      </td>
    </tr>
  </table>
</body>
</html>"""
