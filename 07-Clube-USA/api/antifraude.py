"""
Anti-fraude na camada de registro.
Blocklist de domínios de email descartáveis — MVP.
Para produção com escala, integrar com Kickbox API (kickbox.com) ou similar.
"""

# Domínios de email descartáveis / temporários mais comuns
# Fonte: análise manual de serviços de spam conhecidos
_BLOCKED_DOMAINS: frozenset[str] = frozenset(
    {
        "10minutemail.com",
        "dispostable.com",
        "fakeinbox.com",
        "filzmail.com",
        "getairmail.com",
        "grr.la",
        "guerrillamail.com",
        "guerrillamail.info",
        "guerrillamail.net",
        "guerrillamail.org",
        "guerrillamailblock.com",
        "mailexpire.com",
        "mailinator.com",
        "maildrop.cc",
        "mailnull.com",
        "meltmail.com",
        "sharklasers.com",
        "spam4.me",
        "spambox.us",
        "spamgourmet.com",
        "tempmail.com",
        "throwam.com",
        "tnef.net",
        "trashmail.com",
        "trashmail.me",
        "yopmail.com",
        "yopmail.fr",
    }
)


def is_disposable_email(email: str) -> bool:
    """Retorna True se o email usa um domínio descartável conhecido."""
    try:
        domain = email.rsplit("@", 1)[1].lower()
    except IndexError:
        return False
    return domain in _BLOCKED_DOMAINS
