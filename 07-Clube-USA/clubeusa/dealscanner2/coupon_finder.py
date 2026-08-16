# ============================================================
#  coupon_finder.py — Busca cupons candidatos para um produto
#  no feed de cupons do Slickdeals (RSS, sem credencial).
#
#  Retorna apenas CANDIDATOS. A confirmacao de que o cupom
#  funciona de verdade e responsabilidade do coupon_verifier.py.
# ============================================================

import re
import logging
import feedparser

log = logging.getLogger("coupon_finder")

COUPON_FEED_URL = "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1&forumchoice[]=9"

# Codigo de cupom: 4-20 chars alfanumericos, maiuscula predominante
_CODE_PATTERN = re.compile(r'\bcode\s+([A-Z0-9]{4,20})\b', re.IGNORECASE)


def _title_matches(entry_text: str, product_title: str) -> bool:
    """Match simples por palavras-chave do titulo do produto (>= 1 palavra em comum, min 4 letras)."""
    words = [w.lower() for w in re.findall(r'\w+', product_title) if len(w) >= 4]
    text_lower = entry_text.lower()
    return any(w in text_lower for w in words)


def find_candidates(product_title: str, marketplace: str) -> list[dict]:
    """Busca cupons candidatos para o produto no feed de cupons do Slickdeals."""
    try:
        feed = feedparser.parse(COUPON_FEED_URL)
    except Exception as e:
        log.warning(f"Erro ao buscar feed de cupons: {e}")
        return []

    candidates = []
    for entry in getattr(feed, "entries", []):
        title   = getattr(entry, "title", "") or ""
        summary = getattr(entry, "summary", "") or ""
        full_text = f"{title} {summary}"

        if marketplace.lower() not in full_text.lower():
            continue
        if not _title_matches(full_text, product_title):
            continue

        match = _CODE_PATTERN.search(full_text)
        if not match:
            continue

        candidates.append({
            "code":        match.group(1).upper(),
            "description": title[:200],
            "source":      "slickdeals",
        })

    return candidates
