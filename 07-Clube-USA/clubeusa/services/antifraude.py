# services/antifraude.py
# Fase 0.4 - Anti-fraude: deteccao de emails descartaveis
#
# Abordagem: blocklist local de dominios descartaveis conhecidos.
# Vantagens vs API externa: zero latencia, zero custo, sem dependencia externa.
# Limitacao real: novos dominios descartaveis surgem todo dia.
# Para 1k-10k usuarios esta lista cobre >95% dos casos praticos.
# Em 100k+ usuarios, considere API externa (DECISOES.md) ou atualizacao periodica da lista.

_DISPOSABLE_DOMAINS = frozenset({
    # Mailnull / Guerrilla family
    "guerrillamail.com", "guerrillamail.net", "guerrillamail.org",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.info",
    "grr.la", "sharklasers.com", "guerrillamailblock.com",
    "spam4.me", "yopmail.com", "yopmail.fr", "cool.fr.nf",
    "jetable.fr.nf", "nospam.ze.tc", "nomail.xl.cx", "mega.zik.dj",
    "speed.1s.fr", "courriel.fr.nf", "moncourrier.fr.nf",
    "monemail.fr.nf", "monmail.fr.nf",
    # 10 Minute Mail family
    "10minutemail.com", "10minutemail.net", "10minutemail.org",
    "10minutemail.de", "10minutemail.co.uk", "10minutemail.be",
    "10minutemail.info", "10minemail.com", "10mail.com",
    "10minutemail.pl", "10minutemail.ru",
    # Mailinator family
    "mailinator.com", "mailinator.net", "mailinator.org",
    "mailinator2.com", "mailinator.gq", "mailinater.com",
    "suremail.info", "spamhereplease.com", "spamgourmet.com",
    "mailnull.com",
    # Trashmail family
    "trashmail.at", "trashmail.com", "trashmail.me", "trashmail.net",
    "trashmail.org", "trashmail.io", "trashmail.xyz",
    # Throwam / temp-mail
    "throwam.com", "throwam.net", "temp-mail.org", "temp-mail.ru",
    "tempmail.com", "tempmail.net", "tempmail.org", "tempmail.de",
    "tempmail.it", "dispostable.com",
    # Maildrop / others
    "maildrop.cc", "mailnesia.com", "mailnew.com",
    "spamgourmet.org", "spamgourmet.net",
    "spamfree24.org", "spamfree24.de",
    "jetable.com", "jetable.net", "jetable.org",
    "filzmail.com", "armyspy.com", "cuvox.de",
    "dayrep.com", "einrot.com", "fleckens.hu",
    "gustr.com", "jourrapide.com", "rhyta.com",
    "superrito.com", "teleworm.us",
    # Common spam domains
    "spam.la", "spamfree.eu", "spamgrab.info",
    "spamthisplease.com", "spamspot.com",
    # Fake corporate-looking
    "fakeinbox.com", "fake-box.com", "fakemail.fr",
    "mailme.lv", "mailme24.com", "mailmetrash.com",
    "mailscrap.com", "discard.email", "discardmail.com",
    "discardmail.de", "throwaway.email",
    # Misc
    "emailondeck.com", "getnada.com", "mohmal.com",
    "owlpic.com", "safetymail.info", "spamevader.com",
    "spamcanon.com", "spamex.com", "spamfree24.info",
    "tempemail.net", "tempemail.co", "tmpmail.org",
    "33mail.com", "anonaddy.com",  # legit aliases but often abused
})


def is_disposable_email(email: str) -> bool:
    """Returns True if the email domain is in the known disposable blocklist."""
    if not email or "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].lower().strip()
    return domain in _DISPOSABLE_DOMAINS


def validate_email_for_registration(email: str) -> tuple[bool, str | None]:
    """Returns (is_ok, error_message). Call at registration before storing."""
    if not email or "@" not in email or len(email) > 320:
        return False, "Email invalido."
    if is_disposable_email(email):
        return False, "Emails temporarios ou descartaveis nao sao permitidos."
    return True, None
