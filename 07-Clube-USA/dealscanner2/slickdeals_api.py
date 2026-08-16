# ============================================================
#  slickdeals_api.py — Slickdeals RSS Feed
#
#  Completamente gratuito, sem API key, sem limite.
#  Agrega deals de TODOS os marketplaces:
#  Amazon, Walmart, Target, Costco, BestBuy, etc.
#
#  O melhor: deals ja foram filtrados por humanos reais.
#  So aparecem no feed quando tem votos suficientes.
# ============================================================

import re
import logging
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

import config

log = logging.getLogger("slickdeals")

# Feeds RSS do Slickdeals
FEEDS = {
    "frontpage":   "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1",
    "popular":     "https://slickdeals.net/newsearch.php?mode=popdeals&searcharea=deals&searchin=first&rss=1",
    "electronics": "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1&forumid[]=9",
    "hot":         "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1&forumid[]=30",
}

# Marcas com alta reputacao e volume de vendas
QUALITY_BRANDS = {
    "apple", "sony", "samsung", "lg", "bose", "dyson", "ninja", "instant pot",
    "keurig", "dewalt", "milwaukee", "makita", "kitchenaid", "cuisinart",
    "roomba", "irobot", "shark", "bissell", "breville", "vitamix",
    "nike", "adidas", "under armour", "north face", "patagonia",
    "levi", "columbia", "new balance", "skechers",
    "amazon", "echo", "kindle", "fire tv", "ring",
    "microsoft", "logitech", "corsair", "razer", "anker",
    "fitbit", "garmin", "yeti", "stanley", "hydro flask",
    "lego", "sennheiser", "jbl", "jabra",
    "hp", "dell", "lenovo", "asus",
    "nespresso", "hamilton beach", "black+decker",
    "weber", "traeger", "blackstone",
    "tp-link", "netgear", "ubiquiti", "arlo",
    "coleman", "thermos", "contigo",
}

# Marketplaces que rastreamos via Slickdeals
TRACKED_STORES = {
    "amazon":   "amazon.com",
    "walmart":  "walmart.com",
    "target":   "target.com",
    "bestbuy":  "bestbuy.com",
    "costco":   "costco.com",
    "homedepot":"homedepot.com",
    "kohls":    "kohls.com",
    "macys":    "macys.com",
    "nike":     "nike.com",
    "adidas":   "adidas.com",
}


def fetch_feed(feed_name: str = "popular") -> tuple:
    """
    Busca feed RSS do Slickdeals.
    Retorna (items, erro).
    """
    url = FEEDS.get(feed_name, FEEDS["popular"])
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ClubUSA/1.0; RSS Reader)",
        "Accept":     "application/rss+xml, application/xml, text/xml",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return [], f"Slickdeals RSS erro {resp.status_code}"

        root  = ET.fromstring(resp.content)
        items = root.findall(".//item")
        return items, None

    except Exception as e:
        return [], f"Erro Slickdeals: {e}"


def extract_price(text: str) -> float | None:
    """Extrai preco de texto como '$29.99' ou '29.99'."""
    if not text:
        return None
    match = re.search(r'\$[\d,]+\.?\d*', text)
    if match:
        return float(match.group().replace("$","").replace(",",""))
    return None


def extract_discount(text: str) -> int:
    """Extrai desconto de texto como '50% off' ou '-30%'."""
    match = re.search(r'(\d+)%\s*off', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'-(\d+)%', text)
    if match:
        return int(match.group(1))
    return 0


def detect_store(title: str, description: str) -> str:
    """Detecta qual loja pelo conteudo do deal."""
    text = (title + " " + description).lower()
    for store, domain in TRACKED_STORES.items():
        if domain.split(".")[0] in text or store in text:
            return store
    return "other"


def build_affiliate_url(url: str, store: str) -> str:
    """
    Adiciona tag de afiliado na URL baseado na loja detectada.
    Se nao tiver credencial, retorna URL original.
    """
    if not url:
        return url

    if store == "amazon" and config.AMAZON_PARTNER_TAG and "SEU_" not in config.AMAZON_PARTNER_TAG:
        # Adiciona tag Amazon
        sep = "&" if "?" in url else "?"
        if "tag=" not in url:
            return f"{url}{sep}tag={config.AMAZON_PARTNER_TAG}"

    elif store == "walmart" and config.WALMART_PUBLISHER_ID and "SEU_" not in config.WALMART_PUBLISHER_ID:
        sep = "&" if "?" in url else "?"
        return f"{url}{sep}wmlspartner={config.WALMART_PUBLISHER_ID}"

    return url


def parse_slickdeals_item(item: ET.Element) -> dict | None:
    """Parseia item do RSS Slickdeals para formato padrao."""
    try:
        title = item.findtext("title", "").strip()
        desc  = item.findtext("description", "").strip()
        link  = item.findtext("link", "").strip()
        guid  = item.findtext("guid", link).strip()

        if not title:
            return None

        clean_desc = re.sub(r'<[^>]+>', ' ', desc)
        full_text  = title + " " + clean_desc

        # Formato Slickdeals: "$PRECO* | Nome" — preco no titulo e o atual
        title_price = extract_price(title)
        all_prices  = [float(p.replace(",", "")) for p in re.findall(r'\$\s*([\d,]+\.?\d*)', full_text)]
        price_now   = title_price or (min(all_prices) if all_prices else None)

        if not price_now:
            return None

        # Preco original: primeiro preco maior que o atual
        prices_above = sorted(set(p for p in all_prices if p > price_now * 1.05), reverse=True)
        price_was = prices_above[0] if prices_above else None

        # Tenta extrair via palavras-chave "was/reg/retail"
        if not price_was:
            was_match = re.search(
                r'(?:was|reg(?:ular)?|retail|msrp|list|orig(?:inal)?)\s*:?\s*\$[\d,]+\.?\d*',
                full_text, re.IGNORECASE
            )
            if was_match:
                price_was = extract_price(was_match.group())

        discount_pct = extract_discount(full_text)
        if not discount_pct and price_was and price_was > price_now:
            discount_pct = round((1 - price_now / price_was) * 100)
        if not price_was and discount_pct and price_now:
            price_was = round(price_now / (1 - discount_pct / 100), 2)

        # --- Filtros de qualidade ---
        if discount_pct < config.MIN_DISCOUNT_PCT:
            return None
        if price_now < 25 or price_now > config.MAX_PRICE:   # sem lixo barato
            return None
        savings = (price_was - price_now) if price_was else 0
        if savings < 15:                                       # economia minima $15
            return None
        full_lower = full_text.lower()
        if not any(b in full_lower for b in QUALITY_BRANDS):  # so marcas conhecidas
            return None

        store         = detect_store(title, clean_desc)
        affiliate_url = build_affiliate_url(link, store)
        deal_id       = hashlib.md5(guid.encode()).hexdigest()[:10]

        thumbs_match = re.search(r'(\d+)\s*thumb', full_text, re.IGNORECASE)
        popularity   = int(thumbs_match.group(1)) if thumbs_match else 0

        clean_title = re.sub(r'^\$[\d,]+\.?\d*\*?\s*\|\s*', '', title).strip()

        return {
            "source":       f"slickdeals_{store}",
            "source_id":    deal_id,
            "title":        clean_title[:120],
            "price_now":    price_now,
            "price_was":    price_was,
            "discount_pct": discount_pct,
            "rating":       0.0,
            "reviews":      0,
            "popularity":   popularity,
            "image_url":    None,
            "product_url":  link,
            "affiliate_url": affiliate_url,
            "store":        store,
            "description":  clean_desc[:300],
        }

    except Exception as e:
        log.debug(f"Erro parse Slickdeals: {e}")
        return None


def fetch_all_feeds() -> list:
    """
    Busca todos os feeds e retorna lista de deals parseados.
    Deduplica por source_id.
    """
    all_items = []
    seen_ids  = set()

    for feed_name in ["popular", "frontpage", "hot"]:
        items, err = fetch_feed(feed_name)
        if err:
            log.warning(f"Feed '{feed_name}': {err}")
            continue

        for item in items:
            parsed = parse_slickdeals_item(item)
            if parsed and parsed["source_id"] not in seen_ids:
                seen_ids.add(parsed["source_id"])
                all_items.append(parsed)

        log.info(f"Slickdeals '{feed_name}': {len(items)} itens no feed")

    log.info(f"Slickdeals total: {len(all_items)} deals unicos")
    return all_items
