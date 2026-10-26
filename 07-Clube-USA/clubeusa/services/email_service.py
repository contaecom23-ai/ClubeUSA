# ============================================================
#  services/email_service.py — Clube USA
#  Envio de email transacional
#
#  Dev: loga o link (sem envio real — ENVIRONMENT != production)
#  Prod: usa SendGrid (SENDGRID_API_KEY) ou SMTP generico
#        (SMTP_HOST + SMTP_USER + SMTP_PASS)
#
#  Variáveis de ambiente em produção (uma das opções):
#    Opção A — SendGrid:  SENDGRID_API_KEY, FROM_EMAIL
#    Opção B — SMTP:      SMTP_HOST, SMTP_PORT (def 587), SMTP_USER, SMTP_PASS, FROM_EMAIL
# ============================================================

import os
import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")

FROM_EMAIL = os.environ.get("FROM_EMAIL", "noreply@clubeusa.com")
FROM_NAME  = "Clube USA"


# ============================================================
#  TRANSPORTE
# ============================================================

def _send_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if not all([smtp_host, smtp_user, smtp_pass]):
        log.error("SMTP nao configurado — email nao enviado para %s", to_email)
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"]      = to_email
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html",  "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.login(smtp_user, smtp_pass)
            s.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        log.info("Email enviado (SMTP) para %s: %s", to_email, subject)
        return True
    except Exception as exc:
        log.error("Falha SMTP para %s: %s", to_email, exc)
        return False


def _send_sendgrid(to_email: str, subject: str, html_body: str) -> bool:
    api_key = os.environ.get("SENDGRID_API_KEY")
    if not api_key:
        return False
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg  = sendgrid.SendGridAPIClient(api_key=api_key)
        msg = Mail(
            from_email=(FROM_EMAIL, FROM_NAME),
            to_emails=to_email,
            subject=subject,
            html_content=html_body,
        )
        resp = sg.send(msg)
        log.info("Email enviado (SendGrid) para %s: status %s", to_email, resp.status_code)
        return resp.status_code in (200, 202)
    except ImportError:
        log.warning("sendgrid nao instalado — adicione ao requirements.txt")
        return False
    except Exception as exc:
        log.error("SendGrid erro para %s: %s", to_email, exc)
        return False


def _send(to_email: str, subject: str, text_body: str, html_body: str) -> bool:
    """Envia via SendGrid (se configurado) ou SMTP, ou loga em dev."""
    if os.environ.get("ENVIRONMENT", "development") != "production":
        log.info("[DEV EMAIL] Para: %s | Assunto: %s", to_email, subject)
        import re
        for link in re.findall(r'href="([^"]+)"', html_body):
            log.info("[DEV EMAIL] Link: %s", link)
        return True

    if os.environ.get("SENDGRID_API_KEY"):
        return _send_sendgrid(to_email, subject, html_body)

    return _send_smtp(to_email, subject, text_body, html_body)


# ============================================================
#  TEMPLATES
# ============================================================

def send_confirmation_email(to_email: str, member_name: str, confirm_url: str) -> bool:
    """Envia email de confirmação de cadastro (chamado pelo router email_confirmation)."""
    name = member_name or "membro"
    subject = "Confirme seu email — Clube USA"

    text = (
        f"Clube USA\n\nOlá {name}!\n\n"
        f"Confirme seu email clicando no link abaixo:\n{confirm_url}\n\n"
        "Link válido por 24 horas.\n"
        "Se você não criou uma conta, ignore este email."
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
          O maior clube de ofertas para latinos nos EUA</p>
      </td></tr>
      <tr><td style="padding:36px 32px">
        <h2 style="color:#0D1B3E;margin:0 0 12px;font-size:20px">Confirme seu email</h2>
        <p style="color:#374151;line-height:1.6;margin:0 0 28px">
          Olá {safe_name}! Clique no botão abaixo para confirmar seu endereço de email.</p>
        <a href="{safe_url}"
           style="display:inline-block;background:#B0202F;color:#fff;padding:14px 28px;
                  border-radius:8px;text-decoration:none;font-weight:700;font-size:15px">
          ✓ Confirmar Email
        </a>
        <p style="color:#6B7280;font-size:13px;margin:28px 0 0;line-height:1.5">
          Este link expira em 24 horas.<br>
          Se você não criou uma conta no Clube USA, ignore este email.<br><br>
          Ou cole este link no navegador:<br>
          <a href="{safe_url}" style="color:#B0202F;word-break:break-all">{safe_url}</a>
        </p>
      </td></tr>
      <tr><td style="background:#f9fafb;padding:20px 32px;border-top:1px solid #e5e7eb">
        <p style="color:#9ca3af;font-size:12px;margin:0">
          © 2026 Clube USA ·
          <a href="https://clubeusa.com" style="color:#9ca3af">clubeusa.com</a>
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body></html>"""
