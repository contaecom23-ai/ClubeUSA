# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais via SMTP
# ============================================================

import logging
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_service")


def send_confirmation_email(to_email: str, member_name: str, confirm_url: str) -> bool:
    """
    Envia email de confirmacao de endereco.
    Dev: apenas loga a URL.
    Prod: usa SMTP_HOST/PORT/USER/PASS + FROM_EMAIL.
    Retorna True se enviado com sucesso, False caso contrario.
    """
    if os.environ.get("ENVIRONMENT", "development") != "production":
        log.info(f"[DEV] Confirmacao de email para {to_email}: {confirm_url}")
        return True

    smtp_host = os.environ.get("SMTP_HOST", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    from_email = os.environ.get("FROM_EMAIL", smtp_user)

    if not smtp_host or not smtp_user:
        log.warning("SMTP nao configurado — email nao enviado.")
        return False

    first_name = member_name.split()[0] if member_name else "Membro"

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: system-ui, sans-serif; background: #f8fafc; margin: 0; padding: 0; }}
    .container {{ max-width: 520px; margin: 40px auto; background: white;
                  border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,.1); }}
    .header  {{ background: #0f172a; padding: 32px; text-align: center; }}
    .header h1 {{ color: #fbbf24; font-size: 1.4rem; margin: 0; }}
    .body    {{ padding: 32px; }}
    .body p  {{ color: #475569; line-height: 1.7; }}
    .btn     {{ display: inline-block; margin: 24px 0; padding: 14px 32px;
                background: #fbbf24; color: #0f172a; border-radius: 8px;
                text-decoration: none; font-weight: 700; font-size: 1rem; }}
    .footer  {{ padding: 16px 32px; background: #f1f5f9; font-size: .8rem; color: #94a3b8; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1>Clube USA</h1></div>
    <div class="body">
      <p>Ola, <strong>{first_name}</strong>!</p>
      <p>Para ativar sua conta e ter acesso completo aos beneficios do Clube USA,
         confirme seu endereco de email clicando no botao abaixo:</p>
      <a href="{confirm_url}" class="btn">Confirmar Email</a>
      <p style="font-size:.85rem;color:#94a3b8;">
        Se voce nao criou uma conta no Clube USA, ignore este email.<br>
        Este link expira em 24 horas.
      </p>
    </div>
    <div class="footer">Clube USA &mdash; sua comunidade brasileira nos EUA</div>
  </div>
</body>
</html>"""

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Confirme seu email — Clube USA"
        msg["From"]    = f"Clube USA <{from_email}>"
        msg["To"]      = to_email
        msg.attach(MIMEText(f"Confirme seu email: {confirm_url}", "plain"))
        msg.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        log.info(f"Email de confirmacao enviado para {to_email[:4]}***")
        return True

    except Exception as e:
        log.error(f"Falha ao enviar email: {e}")
        return False
