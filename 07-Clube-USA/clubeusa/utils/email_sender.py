# ============================================================
#  utils/email_sender.py — Clube USA
#  Envio de email com suporte a Resend e SendGrid.
#  Em dev (sem chaves), loga o link no console.
# ============================================================

import os
import logging

log = logging.getLogger("email_sender")


def send_email_confirmation(to_email: str, confirm_url: str, member_name: str = "") -> bool:
    """
    Envia email de confirmação de endereço.

    Returns True se enviado (ou logado em dev), False em falha real.

    Providers suportados (via env vars):
      RESEND_API_KEY   → Resend  (recomendado; 3.000/mês grátis)
      SENDGRID_API_KEY → SendGrid

    Se nenhum estiver configurado, loga o link (modo dev).
    """
    subject = "Confirme seu email — Clube USA"
    greeting = f"Olá{', ' + member_name if member_name else ''}!"
    html_body = f"""
<p>{greeting}</p>
<p>Clique no botão abaixo para confirmar seu endereço de email no <strong>Clube USA</strong>:</p>
<p style="text-align:center;margin:32px 0">
  <a href="{confirm_url}"
     style="background:#1a73e8;color:#fff;padding:14px 28px;border-radius:6px;
            text-decoration:none;font-weight:bold;font-size:16px">
    Confirmar email
  </a>
</p>
<p>O link expira em <strong>24 horas</strong>.</p>
<p>Se você não se cadastrou no Clube USA, ignore este email.</p>
<hr/>
<p style="font-size:12px;color:#666">
  Clube USA · Para imigrantes brasileiros nos EUA<br/>
  <a href="{confirm_url}">{confirm_url}</a>
</p>
"""
    text_body = (
        f"{greeting}\n\n"
        f"Confirme seu email no Clube USA acessando o link abaixo:\n"
        f"{confirm_url}\n\n"
        f"O link expira em 24 horas.\n"
        f"Se você não se cadastrou, ignore este email."
    )

    resend_key   = os.environ.get("RESEND_API_KEY", "")
    sendgrid_key = os.environ.get("SENDGRID_API_KEY", "")
    from_email   = os.environ.get("EMAIL_FROM", "noreply@clubeusa.com")

    if resend_key:
        return _send_resend(resend_key, from_email, to_email, subject, html_body, text_body)

    if sendgrid_key:
        return _send_sendgrid(sendgrid_key, from_email, to_email, subject, html_body, text_body)

    # Dev mode — log the link, don't fail
    log.info(
        "[DEV] Email de confirmação NÃO enviado (sem RESEND_API_KEY/SENDGRID_API_KEY). "
        f"Link para {to_email}: {confirm_url}"
    )
    return True


def _send_resend(api_key: str, from_email: str, to: str,
                 subject: str, html: str, text: str) -> bool:
    import urllib.request, urllib.error, json

    payload = json.dumps({
        "from":    from_email,
        "to":      [to],
        "subject": subject,
        "html":    html,
        "text":    text,
    }).encode()

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"Resend OK ({resp.status}) para {to}")
            return True
    except urllib.error.HTTPError as e:
        log.error(f"Resend HTTP {e.code} para {to}: {e.read()}")
        return False
    except Exception as e:
        log.error(f"Resend erro para {to}: {e}")
        return False


def _send_sendgrid(api_key: str, from_email: str, to: str,
                   subject: str, html: str, text: str) -> bool:
    import urllib.request, urllib.error, json

    payload = json.dumps({
        "personalizations": [{"to": [{"email": to}]}],
        "from":    {"email": from_email},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text},
            {"type": "text/html",  "value": html},
        ],
    }).encode()

    req = urllib.request.Request(
        "https://api.sendgrid.com/v3/mail/send",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            log.info(f"SendGrid OK ({resp.status}) para {to}")
            return True
    except urllib.error.HTTPError as e:
        log.error(f"SendGrid HTTP {e.code} para {to}: {e.read()}")
        return False
    except Exception as e:
        log.error(f"SendGrid erro para {to}: {e}")
        return False
