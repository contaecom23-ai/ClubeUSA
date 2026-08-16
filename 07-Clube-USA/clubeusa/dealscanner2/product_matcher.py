# ============================================================
#  product_matcher.py — Identifica marketplace de origem e
#  busca o mesmo produto (por titulo) nos demais marketplaces
#  suportados.
#
#  v1 suporta: amazon, walmart, bestbuy.
#  Target nao tem API de busca por produto (ver target_api.py) —
#  fica fora ate ter uma fonte de dados viavel.
# ============================================================

import re
import logging

import config
from amazon_api  import get_item_by_asin
from walmart_api import search_walmart, parse_walmart_item
from bestbuy_api  import search_bestbuy, parse_bestbuy_item

log = logging.getLogger("product_matcher")

SUPPORTED_SOURCES = ("amazon", "walmart", "bestbuy")

_PATTERNS = [
    ("amazon",  re.compile(r'amazon\.com.*?/dp/([A-Z0-9]{10})')),
    ("amazon",  re.compile(r'amazon\.com.*?/gp/product/([A-Z0-9]{10})')),
    ("walmart", re.compile(r'walmart\.com/ip/[^/]+/(\d+)')),
    ("bestbuy", re.compile(r'bestbuy\.com/site/[^/]+/(\d+)\.p')),
]


def identify_source(url: str) -> tuple[str, str]:
    """Detecta o marketplace pela URL e extrai o ID do produto."""
    for source, pattern in _PATTERNS:
        m = pattern.search(url)
        if m:
            return source, m.group(1)

    if "target.com" in url.lower():
        raise ValueError(
            "Target ainda não é suportado — use um link direto da Amazon, Walmart ou BestBuy."
        )

    raise ValueError(
        "Link não reconhecido. Use um link direto de produto da Amazon, Walmart ou BestBuy."
    )


def fetch_source_details(source: str, source_id: str) -> dict:
    """Busca titulo/preco/imagem do produto na fonte de origem."""
    if source == "amazon":
        item, err = get_item_by_asin(
            config.AMAZON_ACCESS_KEY, config.AMAZON_SECRET_KEY,
            config.AMAZON_PARTNER_TAG, source_id,
        )
        if err:
            raise ValueError(f"Não foi possível buscar o produto na Amazon: {err}")
        listings = item.get("Offers", {}).get("Listings", [])
        price = listings[0]["Price"]["Amount"] if listings else None
        return {
            "title":     item.get("ItemInfo", {}).get("Title", {}).get("DisplayValue", ""),
            "price":     float(price) if price is not None else None,
            "image_url": item.get("Images", {}).get("Primary", {}).get("Medium", {}).get("URL"),
            "url":       f"https://www.amazon.com/dp/{source_id}?tag={config.AMAZON_PARTNER_TAG}",
        }

    if source == "walmart":
        items, err = search_walmart(source_id, num_items=1)
        if err or not items:
            raise ValueError(f"Não foi possível buscar o produto na Walmart: {err or 'não encontrado'}")
        raw = parse_walmart_item(items[0])
        if not raw:
            raise ValueError("Não foi possível ler os dados do produto na Walmart.")
        return {
            "title": raw["title"], "price": raw["price_now"],
            "image_url": raw.get("image_url"), "url": raw["affiliate_url"],
        }

    if source == "bestbuy":
        items, err = search_bestbuy(source_id, num_items=1)
        if err or not items:
            raise ValueError(f"Não foi possível buscar o produto na BestBuy: {err or 'não encontrado'}")
        raw = parse_bestbuy_item(items[0])
        if not raw:
            raise ValueError("Não foi possível ler os dados do produto na BestBuy.")
        return {
            "title": raw["title"], "price": raw["price_now"],
            "image_url": raw.get("image_url"), "url": raw["affiliate_url"],
        }

    raise ValueError(f"Fonte '{source}' não suportada.")


def find_offers(title: str, exclude_source: str) -> list[dict]:
    """Busca o titulo do produto nos outros marketplaces suportados."""
    offers = []

    if exclude_source != "walmart":
        try:
            items, err = search_walmart(title, num_items=3)
            if not err:
                for item in (items or []):
                    raw = parse_walmart_item(item)
                    if raw and raw.get("price_now") is not None:
                        offers.append({
                            "marketplace": "walmart",
                            "price":       raw["price_now"],
                            "url":         raw["affiliate_url"],
                        })
                        break
        except Exception as e:
            log.warning(f"find_offers walmart falhou: {e}")

    if exclude_source != "bestbuy":
        try:
            items, err = search_bestbuy(title, num_items=3)
            if not err:
                for item in (items or []):
                    raw = parse_bestbuy_item(item)
                    if raw and raw.get("price_now") is not None:
                        offers.append({
                            "marketplace": "bestbuy",
                            "price":       raw["price_now"],
                            "url":         raw["affiliate_url"],
                        })
                        break
        except Exception as e:
            log.warning(f"find_offers bestbuy falhou: {e}")

    return offers
