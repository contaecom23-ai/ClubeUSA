# ============================================================
#  coupon_verifier.py — Confirma se um cupom funciona de
#  verdade, simulando o carrinho no site de destino.
#
#  v1: driver completo apenas para Amazon. Demais marketplaces
#  retornam None (nao verificavel) ate terem driver proprio.
#
#  Qualquer falha (timeout, CAPTCHA, mudanca de HTML) resulta
#  em None — nunca propaga excecao para o chamador.
# ============================================================

import re
import sys
import logging
from playwright.sync_api import sync_playwright

log = logging.getLogger("coupon_verifier")

_PRICE_RE = re.compile(r'\$?([\d,]+\.\d{2})')


def _parse_price(text: str) -> float | None:
    m = _PRICE_RE.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None


def _verify_amazon(code: str, product_url: str) -> bool:
    """
    Abre o produto, adiciona ao carrinho, aplica o codigo de cupom,
    e compara o total antes/depois. Retorna True se o total caiu.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page    = context.new_page()
        try:
            page.goto(product_url, timeout=20000)
            page.click("#add-to-cart-button", timeout=10000)
            page.goto("https://www.amazon.com/gp/cart/view.html", timeout=20000)

            page.wait_for_selector("#sc-subtotal-amount-buybox", timeout=10000)
            total_before = _parse_price(page.text_content("#sc-subtotal-amount-buybox"))

            page.click("[data-name='gc-form-toggle']", timeout=10000)
            page.fill("#gc-redemption-input", code)
            page.click("#gc-redemption-apply-button", timeout=10000)

            page.wait_for_selector("#sc-subtotal-amount-buybox", timeout=10000)
            total_after = _parse_price(page.text_content("#sc-subtotal-amount-buybox"))

            if total_before is None or total_after is None:
                return False
            return total_after < total_before
        finally:
            context.close()
            browser.close()


_DRIVERS = {
    "amazon": "_verify_amazon",
}


def verify(marketplace: str, code: str, product_url: str) -> bool | None:
    """
    Verifica se o cupom `code` funciona de verdade em `product_url`.
    Retorna True/False se conseguiu testar, None se nao for verificavel
    (marketplace sem driver, ou falha na automacao).
    """
    driver_name = _DRIVERS.get(marketplace.lower())
    if not driver_name:
        return None

    # Resolvido em tempo de chamada (via modulo) para respeitar mocks/patches.
    driver = getattr(sys.modules[__name__], driver_name)

    try:
        return driver(code, product_url)
    except Exception as e:
        log.warning(f"Verificacao de cupom falhou ({marketplace}, {code}): {e}")
        return None
