# ============================================================
#  services/email_service.py — Clube USA
#  Envio de email via SMTP. Configurar via env vars:
#    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
# ============================================================

import os
import ssl
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

log = logging.getLogger("email_service")


def send_verification_email(to_email: str, token: str, app_url: str) -> bool:
    """
    Envia email de confirmacao de endereco.
    Em dev (sem SMTP configurado): loga o token e retorna False.
    Retorna True se o email foi enviado com sucesso.
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_user = os.environ.get("SMTP_USER", "")

    if not smtp_host or not smtp_user:
        log.info(f"[DEV] Email verification token (SMTP nao configurado): {token[:12]}...")
        return False

    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_pass = os.environ.get("SMTP_PASS", "")
    from_email = os.environ.get("FROM_EMAIL", smtp_user)

    verify_url = f"{app_url}/auth/email/confirm?token={token}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Confirme seu email — Clube USA"
    msg["From"]    = f"Clube USA <{from_email}>"
    msg["To"]      = to_email

    text_body = (
        f"Clique no link abaixo para confirmar seu email no Clube USA:\n\n"
        f"{verify_url}\n\n"
        f"Link valido por 24 horas.\n"
        f"Se voce nao criou uma conta no Clube USA, ignore este email."
    )
    html_body = f"""<!DOCTYPE html>
<html lang="pt-BR"><body style="font-family:sans-serif;max-width:480px;margin:0 auto;padding:24px">
  <img src="{app_url}/assets/logo.png" alt="Clube USA" style="height:40px;margin-bottom:24px">
  <h2 style="color:#1e3a5f">Confirme seu email</h2>
  <p>Clique no botao abaixo para confirmar seu email no <strong>Clube USA</strong>:</p>
  <a href="{verify_url}"
     style="display:inline-block;background:#2563eb;color:white;padding:12px 28px;
            border-radius:6px;text-decoration:none;font-weight:600;margin:8px 0">
    Confirmar Email
  </a>
  <p style="color:#666;font-size:13px;margin-top:24px">
    Link valido por 24 horas.<br>
    Se voce nao criou uma conta no Clube USA, ignore este email.
  </p>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls(context=ctx)
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())
        masked = to_email[:3] + "***@" + to_email.split("@")[-1] if "@" in to_email else "***"
        log.info(f"Email de verificacao enviado para {masked}")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de verificacao: {e}")
        return False
