import logging
from supabase import Client

logger = logging.getLogger(__name__)

# Domínios de email descartável conhecidos.
# Lista não exaustiva — primeira linha de defesa contra cadastros falsos.
# Não bloqueia domínios corporativos/pessoais legítimos.
_DISPOSABLE_DOMAINS: frozenset = frozenset({
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamailblock.com",
    "guerrillamail.info",
    "guerrillamail.biz",
    "guerrillamail.de",
    "guerrillamail.net",
    "guerrillamail.org",
    "tempmail.com",
    "throwaway.email",
    "yopmail.com",
    "yopmail.fr",
    "cool.fr.nf",
    "jetable.fr.nf",
    "sharklasers.com",
    "guerrillamailblock.com",
    "trashmail.com",
    "trashmail.me",
    "trashmail.net",
    "trashmail.at",
    "trashmail.io",
    "dispostable.com",
    "maildrop.cc",
    "spamgourmet.com",
    "getnada.com",
    "temp-mail.org",
    "tempmail.io",
    "fakeinbox.com",
    "mailnull.com",
    "spamfree24.org",
    "spamcorner.com",
    "inoutmail.com",
    "filzmail.com",
    "sogetthis.com",
    "spamthisplease.com",
    "tafmail.com",
    "zetmail.com",
    "spambot.co",
    "mt2014.com",
    "pookmail.com",
    "wegwerfmail.de",
    "boximail.com",
    "binkmail.com",
    "mail-temporaire.fr",
    "tempemail.net",
    "getairmail.com",
    "mailnesia.com",
    "spamevader.com",
    "mailexpire.com",
    "tempr.email",
    "discard.email",
    "spam4.me",
    "spamgourmet.net",
    "spamgourmet.org",
    "0box.eu",
    "contbay.com",
    "damnthespam.com",
    "fakedemail.com",
    "fakeemailgenerator.com",
    "mailmetrash.com",
    "meltmail.com",
    "mintemail.com",
    "mt2009.com",
    "nomail.xl.cx",
    "nowmymail.com",
    "obobbo.com",
    "smellfear.com",
    "spamfree.eu",
    "tempalias.com",
    "temporaryemail.net",
    "temporaryforwarding.com",
    "thisisnotmyrealemail.com",
    "throwam.com",
    "trashdevil.de",
    "uggsrock.com",
    "wetrainbayarea.com",
    "yandex.kiev.ua",
})


def is_disposable_email(email: str) -> bool:
    """Retorna True se o email usa domínio descartável conhecido."""
    parts = email.lower().split("@")
    if len(parts) != 2:
        return False
    return parts[1] in _DISPOSABLE_DOMAINS


def check_valid_registration(supabase: Client, user_id: str) -> dict:
    """
    Verifica se o cadastro é 'válido' para o programa de referrals (Fase 1.3).

    Critérios atuais (Fase 0.4, pré-lançamento):
      1. Email confirmado (auth.users.email_confirmed_at IS NOT NULL)
      2. ZIP code preenchido — proxy de intenção real disponível antes da Fase 1.1

    Extensão planejada (Fase 1.1+): >=1 ação real na plataforma (ver DECISOES.md).
    """
    email_confirmed = False
    try:
        resp = supabase.auth.admin.get_user_by_id(user_id)
        email_confirmed = (
            resp.user is not None
            and getattr(resp.user, "email_confirmed_at", None) is not None
        )
    except Exception as exc:
        logger.warning(
            "check_valid_registration: auth.admin error for %s: %s",
            user_id,
            type(exc).__name__,
        )

    has_real_action = False
    try:
        result = (
            supabase.table("profiles")
            .select("zip_code")
            .eq("id", user_id)
            .single()
            .execute()
        )
        zip_code = ((result.data or {}).get("zip_code") or "").strip()
        has_real_action = bool(zip_code)
    except Exception as exc:
        logger.warning(
            "check_valid_registration: profiles query error for %s: %s",
            user_id,
            type(exc).__name__,
        )

    is_valid = email_confirmed and has_real_action
    reasons: list = []
    if not email_confirmed:
        reasons.append("email_not_confirmed")
    if not has_real_action:
        reasons.append("no_real_action")

    return {
        "is_valid": is_valid,
        "email_confirmed": email_confirmed,
        "has_real_action": has_real_action,
        "reasons": reasons,
    }


def count_valid_registrations_approx(supabase: Client) -> int:
    """
    Contagem aproximada de cadastros válidos para o painel admin.
    Critério simplificado: perfil com ZIP preenchido (não verifica confirmação de email,
    pois isso exigiria N chamadas à admin API — impraticável para contagem em batch).
    Serve como lower-bound do número real de cadastros válidos.
    """
    try:
        result = (
            supabase.table("profiles")
            .select("id", count="exact")
            .neq("zip_code", "")
            .execute()
        )
        count = result.count
        return int(count) if isinstance(count, int) else 0
    except Exception as exc:
        logger.error("count_valid_registrations_approx: %s", type(exc).__name__)
        return 0
