# ============================================================
#  services/email_service.py — Clube USA
#  Envio de emails transacionais via Resend (ou log em dev).
#
#  Configuracao: RESEND_API_KEY + APP_URL no .env
#  Se RESEND_API_KEY nao estiver definida, apenas loga (dev/test).
# ============================================================

import os
import logging

log = logging.getLogger("email_service")

APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")

# ---- Templates -------------------------------------------------------

_CONFIRM_SUBJECT = {
    "pt": "Clube USA — Confirme seu email",
    "es": "Club USA — Confirma tu correo",
}

_CONFIRM_BODY_HTML = {
    "pt": """
<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:32px;">
  <h2 style="color:#1a56db;">Clube USA</h2>
  <p>Olá! Confirme seu endereço de email clicando no botão abaixo.</p>
  <p style="margin:32px 0;">
    <a href="{confirm_url}"
       style="background:#1a56db;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-weight:bold;">
      Confirmar email
    </a>
  </p>
  <p style="color:#666;font-size:13px;">
    Link válido por 24 horas.<br>
    Se não foi você, ignore este email.
  </p>
</div>
""",
    "es": """
<div style="font-family:sans-serif;max-width:560px;margin:auto;padding:32px;">
  <h2 style="color:#1a56db;">Club USA</h2>
  <p>¡Hola! Confirma tu correo electrónico haciendo clic en el botón.</p>
  <p style="margin:32px 0;">
    <a href="{confirm_url}"
       style="background:#1a56db;color:#fff;padding:14px 28px;
              border-radius:6px;text-decoration:none;font-weight:bold;">
      Confirmar correo
    </a>
  </p>
  <p style="color:#666;font-size:13px;">
    Enlace válido por 24 horas.<br>
    Si no fuiste tú, ignora este correo.
  </p>
</div>
""",
}

# ---- Send ------------------------------------------------------------

def send_confirmation_email(to_email: str, token: str, language: str = "pt") -> bool:
    """
    Envia email de confirmacao.
    Retorna True se enviado (ou logado em dev), False se falhou.
    """
    confirm_url = f"{APP_URL}/auth/email/confirm/{token}"
    lang = language if language in ("pt", "es") else "pt"

    subject = _CONFIRM_SUBJECT[lang]
    body_html = _CONFIRM_BODY_HTML[lang].format(confirm_url=confirm_url)

    api_key = os.environ.get("RESEND_API_KEY")

    if not api_key:
        # Dev/test: apenas loga — nao falha o fluxo
        log.info(f"[DEV] Email de confirmacao para {to_email}: {confirm_url}")
        return True

    return _send_via_resend(api_key, to_email, subject, body_html)


def _send_via_resend(api_key: str, to_email: str, subject: str, html: str) -> bool:
    """Envia via API HTTP do Resend (sem dependencia de SDK extra)."""
    import json
    try:
        import requests as req
        from_address = os.environ.get("EMAIL_FROM", "Clube USA <noreply@clubeusa.com>")
        resp = req.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps({
                "from":    from_address,
                "to":      [to_email],
                "subject": subject,
                "html":    html,
            }),
            timeout=10,
        )
        if resp.status_code in (200, 201):
            return True
        log.error(f"Resend erro {resp.status_code}: {resp.text[:200]}")
        return False
    except Exception as e:
        log.error(f"Falha ao enviar email via Resend: {e}")
        return False
