# ============================================================
#  utils/email.py — Clube USA
#  Envio de email via SMTP (qualquer provedor)
#
#  Env vars necessarias (configurar no .env):
#    SMTP_HOST       — ex: smtp.sendgrid.net | smtp.gmail.com | smtp.resend.com
#    SMTP_PORT       — default 587 (STARTTLS)
#    SMTP_USER       — usuario SMTP (ex: apikey para SendGrid)
#    SMTP_PASSWORD   — senha/token SMTP
#    FROM_EMAIL      — remetente (ex: noreply@clubeusa.com)
#
#  Em dev (sem SMTP_HOST configurado), loga o link em vez de enviar.
# ============================================================

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_sender")

_CONFIRMATION_PT = """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="text-align:center;margin-bottom:24px;">
    <h1 style="color:#2563eb;font-size:24px;margin:0;">Clube USA</h1>
  </div>
  <h2 style="color:#1e293b;">Confirme seu email</h2>
  <p style="color:#475569;">Olá! Para garantir o acesso completo ao Clube USA, clique no botão abaixo para confirmar seu endereço de email:</p>
  <p style="text-align:center;margin:32px 0;">
    <a href="{confirm_url}"
       style="background:#2563eb;color:#ffffff;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;display:inline-block;">
      Confirmar meu email
    </a>
  </p>
  <p style="color:#64748b;font-size:13px;">Ou acesse diretamente:<br>
     <a href="{confirm_url}" style="color:#2563eb;">{confirm_url}</a>
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
  <p style="color:#94a3b8;font-size:12px;">
    Este link expira em 24 horas. Se você não criou uma conta no Clube USA, ignore este email com segurança.
  </p>
</div>
"""

_CONFIRMATION_ES = """
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
  <div style="text-align:center;margin-bottom:24px;">
    <h1 style="color:#2563eb;font-size:24px;margin:0;">Club USA</h1>
  </div>
  <h2 style="color:#1e293b;">Confirma tu correo electrónico</h2>
  <p style="color:#475569;">¡Hola! Para garantizar el acceso completo a Club USA, haz clic en el botón de abajo para confirmar tu correo:</p>
  <p style="text-align:center;margin:32px 0;">
    <a href="{confirm_url}"
       style="background:#2563eb;color:#ffffff;padding:14px 32px;border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;display:inline-block;">
      Confirmar mi correo
    </a>
  </p>
  <p style="color:#64748b;font-size:13px;">O accede directamente:<br>
     <a href="{confirm_url}" style="color:#2563eb;">{confirm_url}</a>
  </p>
  <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0;">
  <p style="color:#94a3b8;font-size:12px;">
    Este enlace expira en 24 horas. Si no creaste una cuenta en Club USA, ignora este correo con seguridad.
  </p>
</div>
"""


def send_confirmation_email(
    to_email: str,
    token: str,
    app_url: str,
    language: str = "pt",
) -> bool:
    """
    Envia email de confirmacao via SMTP.

    Retorna True se enviado com sucesso.
    Em dev (sem SMTP configurado) loga o link e retorna False — nao e erro.
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    from_email = os.environ.get("FROM_EMAIL", smtp_user) or "noreply@clubeusa.com"

    confirm_url = f"{app_url}/auth/email/confirm/{token}"

    if not smtp_host or not smtp_user:
        log.info(f"[DEV EMAIL] Confirmacao de email para {to_email}: {confirm_url}")
        return False

    subject = (
        "Confirma tu correo — Club USA"
        if language == "es"
        else "Confirme seu email — Clube USA"
    )
    template = _CONFIRMATION_ES if language == "es" else _CONFIRMATION_PT
    body_html = template.format(confirm_url=confirm_url)

    msg = MIMEMultipart("alternative")
    msg["From"]    = from_email
    msg["To"]      = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())
        log.info(f"Email de confirmacao enviado para {to_email[:3]}***")
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email de confirmacao: {e}")
        return False
