# ============================================================
#  services/email_service.py — Clube USA
#  Abstrai envio de email. Em producao usa SENDGRID_API_KEY.
#  Em dev, loga no console.
#
#  Para producao: set SENDGRID_API_KEY + EMAIL_FROM no .env
#  (ver DECISOES.md — decisao pendente do dono)
# ============================================================

import os
import logging

log = logging.getLogger("email_service")

_FROM_EMAIL = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")
_FROM_NAME  = os.environ.get("EMAIL_FROM_NAME", "Clube USA")
_APP_URL    = os.environ.get("APP_URL", "https://clubeusa.com")


def send_confirmation_email(to_email: str, to_name: str, token: str) -> bool:
    """
    Envia email de confirmacao de cadastro.
    Retorna True se enviado (ou logado em dev), False se falhou.
    """
    confirm_url = f"{_APP_URL}/auth/confirm-email?token={token}"
    subject = "Confirme seu email — Clube USA"
    body_html = _confirmation_html(to_name or "Amigo(a)", confirm_url)
    body_text = (
        f"Ola {to_name or ''}! Confirme seu email clicando no link:\n{confirm_url}\n"
        f"O link expira em 24 horas.\n\nClube USA"
    )
    return _send(to_email, subject, body_html, body_text)


def send_welcome_email(to_email: str, to_name: str, referral_code: str) -> bool:
    """Envia email de boas-vindas apos confirmacao."""
    referral_link = f"{_APP_URL}?ref={referral_code}"
    subject = "Bem-vindo(a) ao Clube USA!"
    body_html = _welcome_html(to_name or "Amigo(a)", referral_link)
    body_text = (
        f"Ola {to_name or ''}! Seja bem-vindo(a) ao Clube USA!\n"
        f"Seu link de indicacao: {referral_link}\n\nClube USA"
    )
    return _send(to_email, subject, body_html, body_text)


# ─── Interno ─────────────────────────────────────────────────

def _send(to_email: str, subject: str, body_html: str, body_text: str) -> bool:
    env = os.environ.get("ENVIRONMENT", "development")
    api_key = os.environ.get("SENDGRID_API_KEY", "")

    if env != "production" or not api_key:
        log.info(
            "[DEV] Email nao enviado (sem SENDGRID_API_KEY). "
            f"Para: {to_email} | Assunto: {subject}\n{body_text}"
        )
        return True  # em dev, considera enviado

    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail, Email, To, Content

        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=Email(_FROM_EMAIL, _FROM_NAME),
            to_emails=To(to_email),
            subject=subject,
            html_content=Content("text/html", body_html),
        )
        message.add_content(Content("text/plain", body_text))
        resp = sg.client.mail.send.post(request_body=message.get())
        if resp.status_code not in (200, 202):
            log.error(f"SendGrid retornou {resp.status_code} para {to_email}")
            return False
        return True
    except Exception as e:
        log.error(f"Falha ao enviar email para {to_email}: {e}")
        return False


def _confirmation_html(name: str, confirm_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Confirme seu email</title></head>
<body style="font-family:sans-serif;background:#f5f5f5;padding:40px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h1 style="color:#2563EB;font-size:22px">Clube USA 🇺🇸🇧🇷</h1>
    <p>Ola, <strong>{name}</strong>!</p>
    <p>Clique no botao abaixo para confirmar seu email e ativar sua conta:</p>
    <a href="{confirm_url}"
       style="display:inline-block;background:#2563EB;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin:16px 0">
      Confirmar email
    </a>
    <p style="color:#666;font-size:13px">Este link expira em 24 horas.<br>Se nao foi voce, ignore este email.</p>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="color:#999;font-size:12px">Clube USA — comunidade de brasileiros nos EUA</p>
  </div>
</body>
</html>"""


def _welcome_html(name: str, referral_link: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><title>Bem-vindo ao Clube USA</title></head>
<body style="font-family:sans-serif;background:#f5f5f5;padding:40px">
  <div style="max-width:520px;margin:0 auto;background:#fff;border-radius:12px;padding:40px;box-shadow:0 2px 8px rgba(0,0,0,.08)">
    <h1 style="color:#2563EB;font-size:22px">Bem-vindo(a) ao Clube USA! 🎉</h1>
    <p>Ola, <strong>{name}</strong>!</p>
    <p>Sua conta foi confirmada. Voce agora faz parte da maior comunidade de brasileiros nos EUA.</p>
    <p>Compartilhe seu link de indicacao e ganhe pontos:</p>
    <a href="{referral_link}"
       style="display:inline-block;background:#059669;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:bold;margin:16px 0">
      Meu link de indicacao
    </a>
    <hr style="border:none;border-top:1px solid #eee;margin:24px 0">
    <p style="color:#999;font-size:12px">Clube USA — comunidade de brasileiros nos EUA</p>
  </div>
</body>
</html>"""
