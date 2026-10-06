# ============================================================
#  utils/email_sender.py — Clube USA
#  Envio de email via SMTP com fallback para log em dev.
#
#  Vars de ambiente necessárias (prod):
#    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS
#    EMAIL_FROM (opcional, default = SMTP_USER)
#    APP_URL (base para links de confirmação)
#
#  Em dev (SMTP_HOST ausente): loga o link no terminal.
# ============================================================

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

log = logging.getLogger("email_sender")

_APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")


def _smtp_configured() -> bool:
    return bool(os.environ.get("SMTP_HOST"))


def send_email_verification(to_email: str, token: str, member_name: str = "") -> bool:
    """
    Envia email de confirmação com link de verificação.
    Retorna True se enviou, False se falhou (nunca lança exceção — falha silenciosa
    para não bloquear o cadastro).
    """
    confirm_url = f"{_APP_URL}/verify-email?token={token}"
    subject = "Confirme seu email — Clube USA"
    name_greeting = f"Olá, {member_name}!" if member_name else "Olá!"

    html_body = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="font-family:Arial,sans-serif;background:#f4f4f4;margin:0;padding:20px">
  <div style="max-width:520px;margin:auto;background:#fff;border-radius:8px;overflow:hidden">
    <div style="background:#1B3F6E;padding:24px;text-align:center">
      <h1 style="color:#fff;margin:0;font-size:22px">🇧🇷 Clube USA</h1>
    </div>
    <div style="padding:32px 24px">
      <p style="font-size:16px;color:#333">{name_greeting}</p>
      <p style="color:#555">Clique no botão abaixo para confirmar seu email e ativar sua conta.</p>
      <div style="text-align:center;margin:32px 0">
        <a href="{confirm_url}"
           style="background:#1B3F6E;color:#fff;text-decoration:none;
                  padding:14px 28px;border-radius:6px;font-size:15px;font-weight:bold">
          Confirmar email
        </a>
      </div>
      <p style="color:#888;font-size:13px">
        Ou copie este link no navegador:<br>
        <a href="{confirm_url}" style="color:#1B3F6E;word-break:break-all">{confirm_url}</a>
      </p>
      <p style="color:#aaa;font-size:12px;margin-top:24px">
        Este link expira em 24 horas. Se você não criou esta conta, ignore este email.
      </p>
    </div>
  </div>
</body>
</html>
"""
    text_body = (
        f"{name_greeting}\n\n"
        f"Confirme seu email no Clube USA:\n{confirm_url}\n\n"
        "Este link expira em 24 horas."
    )

    if not _smtp_configured():
        log.warning(
            "[EMAIL DEV] SMTP não configurado — link de confirmação:\n  %s",
            confirm_url,
        )
        return True  # em dev, simula envio bem-sucedido

    try:
        host = os.environ["SMTP_HOST"]
        port = int(os.environ.get("SMTP_PORT", "587"))
        user = os.environ["SMTP_USER"]
        password = os.environ["SMTP_PASS"]
        from_addr = os.environ.get("EMAIL_FROM", user)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Clube USA <{from_addr}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_body, "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(host, port, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(user, password)
            server.sendmail(from_addr, [to_email], msg.as_string())

        log.info("Email de verificação enviado para hash=%s", _partial_hash(to_email))
        return True

    except Exception as exc:
        log.error("Falha ao enviar email de verificação: %s", exc)
        return False


def _partial_hash(email: str) -> str:
    """Loga apenas os primeiros 8 chars do hash — sem expor email real."""
    import hashlib
    return hashlib.sha256(email.encode()).hexdigest()[:8]
