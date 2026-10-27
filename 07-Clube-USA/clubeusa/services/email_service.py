# ============================================================
#  services/email_service.py — Clube USA
#  Envio de email transacional (confirmacao de cadastro)
#
#  Dev: loga o link (sem envio real — ENVIRONMENT != production)
#  Prod: usa Resend | SendGrid | SMTP generico
#
#  Variaveis de ambiente (uma das opcoes):
#    Opcao A — Resend:    EMAIL_PROVIDER=resend  EMAIL_API_KEY=re_...  EMAIL_FROM=...
#    Opcao B — SendGrid:  SENDGRID_API_KEY=SG.xxx  FROM_EMAIL=...
#    Opcao C — SMTP:      SMTP_HOST  SMTP_PORT(587)  SMTP_USER  SMTP_PASS  FROM_EMAIL
# ============================================================

import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")

FROM_EMAIL = os.environ.get("FROM_EMAIL", os.environ.get("EMAIL_FROM", "noreply@clubeusa.com"))
FROM_NAME  = "Clube USA"


# ============================================================
#  TRANSPORTES
# ============================================================

def _send_resend(to_email: str, subject: str, html_body: str) -> bool:
    import requests
    api_key   = os.environ.get("EMAIL_API_KEY", "")
    from_addr = os.environ.get("EMAIL_FROM", FROM_EMAIL)
    if not api_key:
        log.error("EMAIL_API_KEY nao configurado para Resend.")
        return False
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"from": from_addr, "to": [to_email], "subject": subject, "html": html_body},
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Email enviado (Resend) para %s", to_email)
        return True
    except Exception as exc:
        log.error("Resend falhou para %s: %s", to_email, exc)
        return False


def _send_sendgrid(to_email: str, subject: str, html_body: str) -> bool:
    """SendGrid via requests — sem dependencia extra (nao requer sdk sendgrid)."""
    import requests
    api_key   = os.environ.get("SENDGRID_API_KEY", os.environ.get("EMAIL_API_KEY", ""))
    from_addr = os.environ.get("FROM_EMAIL", FROM_EMAIL)
    if not api_key:
        log.error("SENDGRID_API_KEY nao configurado.")
        return False
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_addr, "name": FROM_NAME},
                "subject": subject,
                "content": [{"type": "text/html", "value": html_body}],
            },
            timeout=10,
        )
        resp.raise_for_status()
        log.info("Email enviado (SendGrid) para %s", to_email)
        return True
    except Exception as exc:
        log.error("SendGrid falhou para %s: %s", to_email, exc)
        return False


def _send_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("FROM_EMAIL", FROM_EMAIL)

    if not all([smtp_host, smtp_user, smtp_pass]):
        log.error("SMTP nao configurado (faltam SMTP_HOST, SMTP_USER ou SMTP_PASS).")
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{FROM_NAME} <{from_addr}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(smtp_user, smtp_pass)
            s.sendmail(from_addr, [to_email], msg.as_string())
        log.info("Email enviado (SMTP) para %s", to_email)
        return True
    except Exception as exc:
        log.error("SMTP falhou para %s: %s", to_email, exc)
        return False


def _send(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """Orquestra envio em dev (log) ou prod (Resend | SendGrid | SMTP)."""
    if os.environ.get("ENVIRONMENT", "development") != "production":
        import re
        log.info("[DEV EMAIL] Para: %s | Assunto: %s", to_email, subject)
        for link in re.findall(r'href="([^"]+)"', html_body):
            log.info("[DEV EMAIL] Link: %s", link)
        return True

    provider = os.environ.get("EMAIL_PROVIDER", "").lower()
    if provider == "resend":
        return _send_resend(to_email, subject, html_body)
    if provider == "sendgrid" or os.environ.get("SENDGRID_API_KEY"):
        return _send_sendgrid(to_email, subject, html_body)
    return _send_smtp(to_email, subject, text_body, html_body)


# ============================================================
#  API PUBLICA
# ============================================================

def send_confirmation_email(to_email: str, member_name: str = "", confirm_url: str = "") -> bool:
    """
    Envia email de confirmacao de cadastro.

    Args:
        to_email:    endereco de destino
        member_name: nome do membro (opcional, para personalizar o email)
        confirm_url: URL com token de confirmacao
    """
    name    = member_name or "membro"
    subject = "Confirme seu email — Clube USA"
    text    = (
        f"Clube USA\n\nOla {name}!\n\n"
        f"Confirme seu email clicando no link abaixo:\n{confirm_url}\n\n"
        "Link valido por 24 horas.\n"
        "Se voce nao criou uma conta, ignore este email."
    )
    html = _html_confirmation(name, confirm_url)
    return _send(to_email, subject, text, html)


def _html_confirmation(name: str, url: str) -> str:
    safe_url  = url.replace("&", "&amp;").replace('"', "&quot;")
    safe_name = name.replace("<", "&lt;").replace(">", "&gt;")
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
</head>
<body style="margin:0;padding:0;background:#f3f0e8;font-family:Arial,Helvetica,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f0e8;padding:40px 0">
  <tr><td align="center">
    <table width="600" cellpadding="0" cellspacing="0"
      style="background:#fff;border-radius:12px;overflow:hidden;max-width:600px">
      <tr><td style="background:#0D1B3E;padding:28px 32px">
        <h1 style="margin:0;color:#fff;font-size:24px;font-weight:800">Clube USA</h1>
        <p style="margin:4px 0 0;color:rgba(255,255,255,.6);font-size:13px">
          O maior clube de ofertas para imigrantes brasileiros nos EUA</p>
      </td></tr>
      <tr><td style="padding:36px 32px">
        <h2 style="color:#0D1B3E;margin:0 0 12px;font-size:20px">Confirme seu email</h2>
        <p style="color:#374151;line-height:1.6;margin:0 0 28px">
          Ola {safe_name}! Clique no botao abaixo para confirmar seu endereco de email.</p>
        <a href="{safe_url}"
           style="display:inline-block;background:#B0202F;color:#fff;padding:14px 28px;
                  border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">
          Confirmar Email
        </a>
        <p style="color:#6B7280;font-size:13px;margin:28px 0 0;line-height:1.5">
          Este link expira em 24 horas.<br>
          Se voce nao criou uma conta no Clube USA, ignore este email.<br><br>
          Ou cole este link no navegador:<br>
          <a href="{safe_url}" style="color:#B0202F;word-break:break-all">{safe_url}</a>
        </p>
      </td></tr>
      <tr><td style="background:#f9fafb;padding:20px 32px;border-top:1px solid #e5e7eb">
        <p style="color:#9ca3af;font-size:12px;margin:0">
          &copy; 2026 Clube USA &middot;
          <a href="https://clubeusa.com" style="color:#9ca3af">clubeusa.com</a>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""
