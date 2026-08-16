# Rastreador de Produtos Multi-Marketplace + Verificação de Cupons Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que um membro pago cole o link de um produto (Amazon/Walmart/BestBuy), veja o preço nos outros marketplaces suportados, veja cupons candidatos com selo de "confirmado"/"não confirmado", e continue monitorando esse produto ao longo do tempo com notificação automática.

**Architecture:** Três módulos novos em `dealscanner2/` (`product_matcher.py`, `coupon_finder.py`, `coupon_verifier.py`) reaproveitam os clients de marketplace já existentes. Uma nova camada de serviço (`services/tracked_product_service.py`) grava em três tabelas novas no Supabase. Quatro endpoints novos na API FastAPI expõem isso ao frontend, seguindo o padrão de `services/alert_service.py` + `/alerts/*` já existente. O ciclo de recheck roda dentro do `scheduler.py` existente, a cada 6h.

**Tech Stack:** FastAPI, Supabase (Postgres), Playwright (verificação de cupom via navegador headless), feedparser (já é dependência, usado para achar cupons candidatos via RSS), pytest + pytest-mock (padrão de testes já usado no projeto).

**Spec:** `docs/superpowers/specs/2026-08-16-product-tracker-coupon-verification-design.md`

## Global Constraints

- Todos os endpoints novos de `/products/track*` exigem JWT válido + `require_paid_plan` (mesmo padrão de `/alerts/*` em `clubeusa/api/deps.py`)
- Máximo 10 produtos com `status='active'` por membro (mesmo padrão de `MAX_ACTIVE_ALERTS=10` em `services/alert_service.py`)
- **Correção de escopo em relação à spec, identificada no planejamento:** Target não tem API de busca por produto nem por ID (`dealscanner2/target_api.py` só enriquece links já capturados via Slickdeals RSS, não permite buscar um produto específico). A v1 deste plano implementa **Amazon, Walmart e BestBuy** como fontes/destinos completos. A coluna `source`/`marketplace` no banco mantém `'target'` como valor válido para o schema já não precisar de migration nova quando o suporte a Target for adicionado depois, mas nenhuma task deste plano implementa busca ativa para Target — `identify_source()` recusa links do Target com erro claro na v1.
- `coupon_verifier.py` implementa o driver Playwright completo apenas para **Amazon** na v1 (é o marketplace que os membros mais usam, e serve de referência para os próximos). Walmart e BestBuy retornam `None` (não verificável) através do mesmo dispatcher — nunca lançam exceção, nunca travam o fluxo. Isso é consistente com a regra da spec de que cupons não verificáveis automaticamente aparecem como "não confirmado", nunca como erro.
- Nenhuma chamada de rede real deve rodar durante os testes automatizados — todo teste usa mocks (`pytest-mock`, `unittest.mock.MagicMock`), seguindo o padrão de `tests/test_alert_service.py`
- Arquivos Python novos usam `python -m pytest tests/ -v` a partir de `clubeusa/` para rodar os testes (ver `clubeusa/tests/conftest.py` para o `sys.path` já configurado)

---

### Task 1: Migration SQL — tabelas de rastreamento

**Files:**
- Create: `clubeusa/db/product_tracker_migration.sql`

**Interfaces:**
- Produces: tabelas `tracked_products`, `tracked_product_offers`, `tracked_product_coupons` no Supabase — usadas por todas as tasks seguintes via `services/tracked_product_service.py`

- [ ] **Step 1: Escrever o arquivo de migration**

```sql
-- product_tracker_migration.sql
-- Executar no Supabase SQL Editor

CREATE TABLE tracked_products (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    member_id     UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    source_url    TEXT NOT NULL,
    source        VARCHAR(20) NOT NULL CHECK (source IN ('amazon','walmart','target','bestbuy')),
    source_id     VARCHAR(64) NOT NULL,
    title         TEXT,
    image_url     TEXT,
    status        VARCHAR(20) NOT NULL DEFAULT 'active'
                  CHECK (status IN ('active', 'paused', 'cancelled')),
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tracked_member ON tracked_products (member_id);
CREATE INDEX idx_tracked_active ON tracked_products (status) WHERE status = 'active';

CREATE TABLE tracked_product_offers (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL CHECK (marketplace IN ('amazon','walmart','target','bestbuy')),
    price              NUMERIC(10,2),
    url                TEXT NOT NULL,
    last_checked_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace)
);

CREATE TABLE tracked_product_coupons (
    id                 UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracked_product_id UUID NOT NULL REFERENCES tracked_products(id) ON DELETE CASCADE,
    marketplace        VARCHAR(20) NOT NULL,
    code               VARCHAR(64) NOT NULL,
    description        TEXT,
    source             VARCHAR(40),
    verified           BOOLEAN,
    last_verified_at   TIMESTAMPTZ,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tracked_product_id, marketplace, code)
);

CREATE INDEX idx_coupons_product ON tracked_product_coupons (tracked_product_id);

ALTER TABLE tracked_products ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_product_coupons ENABLE ROW LEVEL SECURITY;

CREATE POLICY tracked_products_own_select ON tracked_products
    FOR SELECT USING (member_id = auth.uid());
CREATE POLICY tracked_products_own_insert ON tracked_products
    FOR INSERT WITH CHECK (member_id = auth.uid());
CREATE POLICY tracked_products_own_update ON tracked_products
    FOR UPDATE USING (member_id = auth.uid());

CREATE POLICY offers_via_product ON tracked_product_offers
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
CREATE POLICY coupons_via_product ON tracked_product_coupons
    FOR SELECT USING (
        tracked_product_id IN (SELECT id FROM tracked_products WHERE member_id = auth.uid())
    );
```

- [ ] **Step 2: Validar sintaxe localmente (sem banco disponível, checagem visual + `psql --dry-run` não existe, então valide com um parser simples)**

Run: `python -c "import re; s=open('clubeusa/db/product_tracker_migration.sql').read(); assert s.count('CREATE TABLE')==3; assert s.count('CREATE POLICY')==5; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add clubeusa/db/product_tracker_migration.sql
git commit -m "feat(db): migration das tabelas de rastreamento multi-marketplace

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

**Nota para quem for rodar em produção:** esta migration precisa ser colada manualmente no SQL Editor do Supabase (mesmo processo do `price_alerts_migration.sql` — ver `README_SETUP.md`). Nenhuma task deste plano executa migrations automaticamente.

---

### Task 2: `amazon_api.py` — buscar item único por ASIN

**Files:**
- Modify: `dealscanner2/amazon_api.py`
- Test: `clubeusa/tests/test_amazon_api.py`

**Interfaces:**
- Consumes: `build_signed_request(access_key, secret_key, partner_tag, payload_dict)` (já existe no mesmo arquivo, linha 36)
- Produces: `get_item_by_asin(access_key, secret_key, partner_tag, asin) -> tuple[dict | None, str | None]` — usado pela Task 3 (`product_matcher.py`) para buscar detalhes do produto de origem quando o link colado é da Amazon

- [ ] **Step 1: Escrever o teste que falha**

```python
# clubeusa/tests/test_amazon_api.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import patch, MagicMock

def test_get_item_by_asin_returns_item_on_200():
    from amazon_api import get_item_by_asin

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ItemsResult": {"Items": [{"ASIN": "B08N5WRWNW", "ItemInfo": {"Title": {"DisplayValue": "Echo Dot"}}}]}
    }
    with patch("amazon_api.requests.post", return_value=mock_resp):
        item, err = get_item_by_asin("AK", "SK", "tag-20", "B08N5WRWNW")

    assert err is None
    assert item["ASIN"] == "B08N5WRWNW"

def test_get_item_by_asin_returns_error_on_404():
    from amazon_api import get_item_by_asin

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.json.return_value = {"Errors": [{"Message": "Item nao encontrado"}]}
    with patch("amazon_api.requests.post", return_value=mock_resp):
        item, err = get_item_by_asin("AK", "SK", "tag-20", "B00000000X")

    assert item is None
    assert "nao encontrado" in err
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd clubeusa && python -m pytest tests/test_amazon_api.py -v`
Expected: `FAIL` — `ImportError: cannot import name 'get_item_by_asin'`

- [ ] **Step 3: Implementar `get_item_by_asin`**

Adicionar ao final de `dealscanner2/amazon_api.py` (reaproveita `build_signed_request`, trocando apenas o payload e o `x-amz-target` — a operação PA-API é `GetItems` em vez de `SearchItems`):

```python
def get_item_by_asin(access_key, secret_key, partner_tag, asin):
    """
    Busca um unico item pelo ASIN (PA-API GetItems).
    Retorna (item_dict, erro).
    """
    payload_dict = {
        "ItemIds":     [asin],
        "PartnerTag":  partner_tag,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.com",
        "Resources": [
            "ItemInfo.Title",
            "Offers.Listings.Price",
            "Offers.Listings.SavingBasis",
            "CustomerReviews.StarRating",
            "CustomerReviews.Count",
            "Images.Primary.Medium",
        ],
    }

    payload, headers = build_signed_request(access_key, secret_key, partner_tag, payload_dict)
    headers["x-amz-target"] = "com.amazon.paapi5.v1.ProductAdvertisingAPIv1.GetItems"

    try:
        resp = requests.post(
            f"https://{HOST}/paapi5/getitems", data=payload, headers=headers, timeout=15
        )
    except requests.RequestException as e:
        return None, f"Erro de rede: {e}"

    if resp.status_code != 200:
        try:
            err = resp.json()
            msg = err.get("Errors", [{}])[0].get("Message", resp.text[:200])
        except Exception:
            msg = resp.text[:200]
        return None, f"API erro {resp.status_code}: {msg}"

    try:
        data = resp.json()
    except Exception:
        return None, "Resposta invalida da API"

    items = data.get("ItemsResult", {}).get("Items", [])
    if not items:
        return None, "Item nao encontrado"
    return items[0], None
```

Nota: `build_signed_request` assina o `canonical_request` usando o path fixo `/paapi5/searchitems` (linha 61 do arquivo original). Como `GetItems` usa um path diferente (`/paapi5/getitems`), extraia o path para um parâmetro da função em vez de deixá-lo hardcoded — ajuste `build_signed_request` assim:

```python
def build_signed_request(access_key, secret_key, partner_tag, payload_dict, path="/paapi5/searchitems", target="SearchItems"):
    ...
    headers_to_sign = {
        "content-encoding": "amz-1.0",
        "content-type":     "application/json; charset=utf-8",
        "host":             HOST,
        "x-amz-date":       amz_date,
        "x-amz-target":     f"com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{target}",
    }
    ...
    canonical_request = "\n".join([
        "POST",
        path,
        "",
        canonical_headers,
        signed_headers,
        _sha256_hex(payload),
    ])
```

E então `get_item_by_asin` chama `build_signed_request(access_key, secret_key, partner_tag, payload_dict, path="/paapi5/getitems", target="GetItems")` sem precisar sobrescrever o header manualmente. Atualize também a chamada existente em `search_items` para passar `target="SearchItems"` (comportamento idêntico ao atual, só explícito).

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd clubeusa && python -m pytest tests/test_amazon_api.py -v`
Expected: `PASS` (2 testes)

- [ ] **Step 5: Rodar a suíte completa para garantir que `search_items` não quebrou**

Run: `cd clubeusa && python -m pytest tests/ -v`
Expected: todos os testes existentes continuam `PASS`

- [ ] **Step 6: Commit**

```bash
git add dealscanner2/amazon_api.py clubeusa/tests/test_amazon_api.py
git commit -m "feat(amazon): adicionar busca de item unico por ASIN (GetItems)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: `product_matcher.py` — identificar fonte e buscar ofertas cruzadas

**Files:**
- Create: `dealscanner2/product_matcher.py`
- Test: `clubeusa/tests/test_product_matcher.py`

**Interfaces:**
- Consumes: `amazon_api.get_item_by_asin` (Task 2), `walmart_api.search_walmart`/`parse_walmart_item`, `bestbuy_api.search_bestbuy`/`parse_bestbuy_item` (já existentes)
- Produces:
  - `identify_source(url: str) -> tuple[str, str]` — retorna `(source, source_id)` ou lança `ValueError` com mensagem clara
  - `fetch_source_details(source: str, source_id: str) -> dict` — retorna `{"title": str, "price": float, "image_url": str|None, "url": str}`, usado pela Task 6 (service layer)
  - `find_offers(title: str, exclude_source: str) -> list[dict]` — retorna lista de `{"marketplace": str, "price": float, "url": str}`, usado pela Task 6

- [ ] **Step 1: Escrever os testes que falham**

```python
# clubeusa/tests/test_product_matcher.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

import pytest
from unittest.mock import patch

# ---- identify_source ----

def test_identify_amazon_dp():
    from product_matcher import identify_source
    source, sid = identify_source("https://www.amazon.com/dp/B08N5WRWNW")
    assert source == "amazon"
    assert sid == "B08N5WRWNW"

def test_identify_walmart_ip():
    from product_matcher import identify_source
    source, sid = identify_source("https://www.walmart.com/ip/Ninja-Air-Fryer/114215867")
    assert source == "walmart"
    assert sid == "114215867"

def test_identify_bestbuy_site():
    from product_matcher import identify_source
    source, sid = identify_source("https://www.bestbuy.com/site/apple-airpods-pro/6501700.p")
    assert source == "bestbuy"
    assert sid == "6501700"

def test_identify_target_raises_not_supported():
    from product_matcher import identify_source
    with pytest.raises(ValueError, match="Target ainda não é suportado"):
        identify_source("https://www.target.com/p/kitchenaid/-/A-14766013")

def test_identify_unknown_url_raises():
    from product_matcher import identify_source
    with pytest.raises(ValueError, match="não reconhecido"):
        identify_source("https://www.google.com/search?q=produto")

# ---- find_offers ----

def test_find_offers_skips_excluded_source_and_aggregates_others(mocker):
    from product_matcher import find_offers

    mocker.patch(
        "product_matcher.search_walmart",
        return_value=([{"raw": "walmart-item"}], None),
    )
    mocker.patch(
        "product_matcher.parse_walmart_item",
        return_value={
            "source": "walmart", "source_id": "1", "title": "Echo Dot",
            "price_now": 24.5, "affiliate_url": "https://walmart.com/ip/1",
        },
    )
    mocker.patch("product_matcher.search_bestbuy", return_value=([], None))

    offers = find_offers("Echo Dot", exclude_source="amazon")

    assert len(offers) == 1
    assert offers[0]["marketplace"] == "walmart"
    assert offers[0]["price"] == 24.5

def test_find_offers_excludes_source_marketplace(mocker):
    from product_matcher import find_offers

    mocker.patch("product_matcher.search_walmart", return_value=([], None))
    mocker.patch("product_matcher.search_bestbuy", return_value=([], None))

    offers = find_offers("Echo Dot", exclude_source="walmart")

    # so bestbuy deveria ter sido chamado, walmart nao
    assert all(o["marketplace"] != "walmart" for o in offers)
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_product_matcher.py -v`
Expected: `FAIL` — `ModuleNotFoundError: No module named 'product_matcher'`

- [ ] **Step 3: Implementar `product_matcher.py`**

```python
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
            "price":     float(price) if price else None,
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
                    if raw and raw.get("price_now"):
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
                    if raw and raw.get("price_now"):
                        offers.append({
                            "marketplace": "bestbuy",
                            "price":       raw["price_now"],
                            "url":         raw["affiliate_url"],
                        })
                        break
        except Exception as e:
            log.warning(f"find_offers bestbuy falhou: {e}")

    return offers
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_product_matcher.py -v`
Expected: `PASS` (7 testes)

- [ ] **Step 5: Commit**

```bash
git add dealscanner2/product_matcher.py clubeusa/tests/test_product_matcher.py
git commit -m "feat(scanner): adicionar product_matcher para busca cross-marketplace

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: `coupon_finder.py` — cupons candidatos via Slickdeals

**Files:**
- Create: `dealscanner2/coupon_finder.py`
- Test: `clubeusa/tests/test_coupon_finder.py`

**Interfaces:**
- Consumes: `feedparser` (já em `requirements.txt`)
- Produces: `find_candidates(title: str, marketplace: str) -> list[dict]` — cada item é `{"code": str, "description": str, "source": str}`, usado pela Task 6

- [ ] **Step 1: Escrever os testes que falham**

```python
# clubeusa/tests/test_coupon_finder.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import MagicMock, patch

def _fake_entry(title, summary):
    e = MagicMock()
    e.title = title
    e.summary = summary
    return e

def test_find_candidates_extracts_code_from_title_and_summary(mocker):
    from coupon_finder import find_candidates

    fake_feed = MagicMock()
    fake_feed.entries = [
        _fake_entry(
            "Amazon: 20% off Echo Dot with code SAVE20ECHO",
            "Use coupon code SAVE20ECHO at checkout for 20% off.",
        ),
        _fake_entry("Unrelated deal about shoes", "no code here"),
    ]
    mocker.patch("coupon_finder.feedparser.parse", return_value=fake_feed)

    candidates = find_candidates("Echo Dot", "amazon")

    assert len(candidates) == 1
    assert candidates[0]["code"] == "SAVE20ECHO"
    assert candidates[0]["source"] == "slickdeals"

def test_find_candidates_returns_empty_when_no_match(mocker):
    from coupon_finder import find_candidates

    fake_feed = MagicMock()
    fake_feed.entries = [_fake_entry("Totally unrelated deal", "no code")]
    mocker.patch("coupon_finder.feedparser.parse", return_value=fake_feed)

    candidates = find_candidates("Echo Dot", "amazon")
    assert candidates == []

def test_find_candidates_handles_feed_error_gracefully(mocker):
    from coupon_finder import find_candidates

    mocker.patch("coupon_finder.feedparser.parse", side_effect=Exception("timeout"))

    candidates = find_candidates("Echo Dot", "amazon")
    assert candidates == []
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_coupon_finder.py -v`
Expected: `FAIL` — `ModuleNotFoundError: No module named 'coupon_finder'`

- [ ] **Step 3: Implementar `coupon_finder.py`**

```python
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
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_coupon_finder.py -v`
Expected: `PASS` (3 testes)

- [ ] **Step 5: Commit**

```bash
git add dealscanner2/coupon_finder.py clubeusa/tests/test_coupon_finder.py
git commit -m "feat(scanner): adicionar coupon_finder (candidatos via Slickdeals RSS)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: `coupon_verifier.py` — verificação real via Playwright (driver Amazon)

**Files:**
- Create: `dealscanner2/coupon_verifier.py`
- Test: `clubeusa/tests/test_coupon_verifier.py`
- Modify: `clubeusa/requirements.txt`

**Interfaces:**
- Consumes: `playwright.sync_api.sync_playwright`
- Produces: `verify(marketplace: str, code: str, product_url: str) -> bool | None` — usado pela Task 6. `None` = não verificável, nunca lança exceção.

- [ ] **Step 1: Adicionar `playwright` ao `requirements.txt`**

```
# Verificacao de cupons (navegador headless)
playwright
```

- [ ] **Step 2: Escrever os testes que falham**

```python
# clubeusa/tests/test_coupon_verifier.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from unittest.mock import patch

def test_verify_returns_none_for_unsupported_marketplace():
    from coupon_verifier import verify
    result = verify("walmart", "CODE123", "https://walmart.com/ip/1")
    assert result is None

def test_verify_returns_true_when_amazon_driver_confirms(mocker):
    from coupon_verifier import verify
    mocker.patch("coupon_verifier._verify_amazon", return_value=True)
    result = verify("amazon", "SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")
    assert result is True

def test_verify_returns_none_when_amazon_driver_raises(mocker):
    from coupon_verifier import verify
    mocker.patch("coupon_verifier._verify_amazon", side_effect=Exception("timeout no playwright"))
    result = verify("amazon", "SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")
    assert result is None

def test_verify_amazon_driver_detects_price_drop():
    from coupon_verifier import _verify_amazon

    class FakePage:
        def __init__(self):
            self.calls = []
        def goto(self, url, **kw): self.calls.append(("goto", url))
        def click(self, sel, **kw): self.calls.append(("click", sel))
        def fill(self, sel, value, **kw): self.calls.append(("fill", sel, value))
        def wait_for_selector(self, sel, **kw): self.calls.append(("wait", sel))
        def text_content(self, sel):
            # primeira leitura = total antes do cupom, segunda = depois
            self._reads = getattr(self, "_reads", 0) + 1
            return "$22.99" if self._reads == 1 else "$18.39"

    class FakeContext:
        def new_page(self): return FakePage()
        def close(self): pass

    class FakeBrowser:
        def new_context(self): return FakeContext()
        def close(self): pass

    class FakeChromium:
        def launch(self, **kw): return FakeBrowser()

    class FakePlaywright:
        chromium = FakeChromium()
        def __enter__(self): return self
        def __exit__(self, *a): pass

    with patch("coupon_verifier.sync_playwright", return_value=FakePlaywright()):
        result = _verify_amazon("SAVE20ECHO", "https://amazon.com/dp/B08N5WRWNW")

    assert result is True
```

- [ ] **Step 3: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_coupon_verifier.py -v`
Expected: `FAIL` — `ModuleNotFoundError: No module named 'coupon_verifier'`

- [ ] **Step 4: Implementar `coupon_verifier.py`**

```python
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
    "amazon": _verify_amazon,
}


def verify(marketplace: str, code: str, product_url: str) -> bool | None:
    """
    Verifica se o cupom `code` funciona de verdade em `product_url`.
    Retorna True/False se conseguiu testar, None se nao for verificavel
    (marketplace sem driver, ou falha na automacao).
    """
    driver = _DRIVERS.get(marketplace.lower())
    if not driver:
        return None

    try:
        return driver(code, product_url)
    except Exception as e:
        log.warning(f"Verificacao de cupom falhou ({marketplace}, {code}): {e}")
        return None
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_coupon_verifier.py -v`
Expected: `PASS` (4 testes)

- [ ] **Step 6: Instalar o Playwright localmente (necessário antes de rodar em produção, não faz parte do CI de testes unitários)**

Run: `pip install playwright && playwright install chromium`
Expected: instala o pacote + o binário do Chromium headless

- [ ] **Step 7: Commit**

```bash
git add dealscanner2/coupon_verifier.py clubeusa/tests/test_coupon_verifier.py clubeusa/requirements.txt
git commit -m "feat(scanner): adicionar coupon_verifier com driver Playwright para Amazon

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: `services/tracked_product_service.py` — camada de dados

**Files:**
- Create: `clubeusa/services/tracked_product_service.py`
- Test: `clubeusa/tests/test_tracked_product_service.py`

**Interfaces:**
- Consumes: `product_matcher.identify_source/fetch_source_details/find_offers` (Task 3), `coupon_finder.find_candidates` (Task 4), `coupon_verifier.verify` (Task 5)
- Produces:
  - `create_tracked_product(member_id: str, url: str) -> dict` — usado pela Task 7 (`POST /products/track`)
  - `list_tracked_products(member_id: str) -> list[dict]` — usado pela Task 7 (`GET /products/track`)
  - `get_tracked_product(tracked_id: str, member_id: str) -> dict | None` — usado pela Task 7 (`GET /products/track/{id}`)
  - `cancel_tracked_product(tracked_id: str, member_id: str) -> bool` — usado pela Task 7 (`DELETE /products/track/{id}`)
  - `refresh_coupons(tracked_id: str)` — usado pela Task 8 (`scheduler.py`), roda `find_candidates` + `verify` e grava em `tracked_product_coupons`

**Nota:** esta task mocka `product_matcher`/`coupon_finder`/`coupon_verifier` inteiros nos testes (eles já têm sua própria suíte nas Tasks 3-5) — aqui o foco é a lógica de persistência e orquestração.

- [ ] **Step 1: Escrever os testes que falham**

```python
# clubeusa/tests/test_tracked_product_service.py
from unittest.mock import MagicMock

MAX = 10

def test_create_tracked_product_raises_on_limit(mocker):
    from services.tracked_product_service import create_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = [{}] * MAX
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    import pytest
    with pytest.raises(ValueError, match="Limite"):
        create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")

def test_create_tracked_product_success(mocker):
    from services.tracked_product_service import create_tracked_product

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []  # sem limite
    mock_sb.table().insert().execute.return_value.data = [{
        "id": "tp-1", "member_id": "m-1", "source": "amazon",
        "source_id": "B08N5WRWNW", "title": "Echo Dot", "status": "active",
    }]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        return_value=("amazon", "B08N5WRWNW"),
    )
    mocker.patch(
        "services.tracked_product_service.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 22.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )
    mocker.patch(
        "services.tracked_product_service.find_offers",
        return_value=[{"marketplace": "walmart", "price": 24.5, "url": "https://walmart.com/ip/1"}],
    )
    mocker.patch("services.tracked_product_service._trigger_coupon_refresh_async")

    result = create_tracked_product("m-1", "https://www.amazon.com/dp/B08N5WRWNW")

    assert result["id"] == "tp-1"
    assert result["title"] == "Echo Dot"
    assert result["offers"][0]["marketplace"] == "amazon"
    assert result["offers"][1]["marketplace"] == "walmart"

def test_create_tracked_product_wraps_matcher_error(mocker):
    from services.tracked_product_service import create_tracked_product

    mock_sb = MagicMock()
    mock_sb.table().select().eq().eq().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.identify_source",
        side_effect=ValueError("Link não reconhecido."),
    )

    import pytest
    with pytest.raises(ValueError, match="não reconhecido"):
        create_tracked_product("m-1", "https://google.com")

def test_cancel_tracked_product_returns_true(mocker):
    from services.tracked_product_service import cancel_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().update().eq().eq().execute.return_value.data = [{"id": "tp-1"}]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    assert cancel_tracked_product("tp-1", "m-1") is True

def test_cancel_tracked_product_not_found_returns_false(mocker):
    from services.tracked_product_service import cancel_tracked_product
    mock_sb = MagicMock()
    mock_sb.table().update().eq().eq().execute.return_value.data = []
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)

    assert cancel_tracked_product("tp-nao-existe", "m-1") is False

def test_refresh_coupons_writes_verified_and_unverified(mocker):
    from services.tracked_product_service import refresh_coupons

    mock_sb = MagicMock()
    mock_sb.table().select().eq().single().execute.return_value.data = {
        "id": "tp-1", "title": "Echo Dot",
    }
    mock_sb.table().select().eq().execute.return_value.data = [
        {"marketplace": "amazon", "url": "https://amazon.com/dp/B08N5WRWNW"},
        {"marketplace": "walmart", "url": "https://walmart.com/ip/1"},
    ]
    mocker.patch("services.tracked_product_service._supabase", return_value=mock_sb)
    mocker.patch(
        "services.tracked_product_service.find_candidates",
        side_effect=[
            [{"code": "SAVE20", "description": "20% off", "source": "slickdeals"}],
            [],
        ],
    )
    mocker.patch("services.tracked_product_service.verify", return_value=True)

    refresh_coupons("tp-1")

    mock_sb.table().upsert.assert_called()
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_tracked_product_service.py -v`
Expected: `FAIL` — `ModuleNotFoundError: No module named 'services.tracked_product_service'`

- [ ] **Step 3: Implementar `services/tracked_product_service.py`**

```python
# ============================================================
#  services/tracked_product_service.py — Clube USA
#  Rastreamento de produto multi-marketplace + cupons
# ============================================================

import os
import sys
import logging
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

from product_matcher import identify_source, fetch_source_details, find_offers
from coupon_finder    import find_candidates
from coupon_verifier  import verify

log = logging.getLogger("tracked_product_service")

MAX_TRACKED_PRODUCTS = 10
RECHECK_VERIFIED_AFTER_DAYS = 7


def _supabase():
    from supabase import create_client
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def _trigger_coupon_refresh_async(tracked_id: str):
    """Dispara refresh_coupons em background (thread) para nao bloquear a resposta da API."""
    import threading
    threading.Thread(target=refresh_coupons, args=(tracked_id,), daemon=True).start()


def create_tracked_product(member_id: str, url: str) -> dict:
    sb = _supabase()

    existing = (
        sb.table("tracked_products")
        .select("id")
        .eq("member_id", member_id)
        .eq("status", "active")
        .execute()
    )
    if len(existing.data) >= MAX_TRACKED_PRODUCTS:
        raise ValueError(f"Limite de {MAX_TRACKED_PRODUCTS} produtos rastreados atingido.")

    source, source_id = identify_source(url)
    details = fetch_source_details(source, source_id)

    inserted = (
        sb.table("tracked_products")
        .insert({
            "member_id":  member_id,
            "source_url": url,
            "source":     source,
            "source_id":  source_id,
            "title":      details["title"],
            "image_url":  details.get("image_url"),
        })
        .execute()
    ).data[0]

    offers = [{"marketplace": source, "price": details["price"], "url": details["url"]}]
    offers += find_offers(details["title"], exclude_source=source)

    for offer in offers:
        sb.table("tracked_product_offers").upsert({
            "tracked_product_id": inserted["id"],
            "marketplace":        offer["marketplace"],
            "price":              offer["price"],
            "url":                offer["url"],
        }, on_conflict="tracked_product_id,marketplace").execute()

    _trigger_coupon_refresh_async(inserted["id"])

    inserted["offers"] = offers
    return inserted


def list_tracked_products(member_id: str) -> list:
    sb = _supabase()
    products = (
        sb.table("tracked_products")
        .select("*")
        .eq("member_id", member_id)
        .neq("status", "cancelled")
        .order("created_at", desc=True)
        .execute()
    ).data

    for p in products:
        p["offers"]  = sb.table("tracked_product_offers").select("*").eq("tracked_product_id", p["id"]).execute().data
        p["coupons"] = sb.table("tracked_product_coupons").select("*").eq("tracked_product_id", p["id"]).execute().data

    return products


def get_tracked_product(tracked_id: str, member_id: str) -> dict | None:
    sb = _supabase()
    result = (
        sb.table("tracked_products")
        .select("*")
        .eq("id", tracked_id)
        .eq("member_id", member_id)
        .execute()
    )
    if not result.data:
        return None

    p = result.data[0]
    p["offers"]  = sb.table("tracked_product_offers").select("*").eq("tracked_product_id", tracked_id).execute().data
    p["coupons"] = sb.table("tracked_product_coupons").select("*").eq("tracked_product_id", tracked_id).execute().data
    return p


def cancel_tracked_product(tracked_id: str, member_id: str) -> bool:
    sb = _supabase()
    result = (
        sb.table("tracked_products")
        .update({"status": "cancelled"})
        .eq("id", tracked_id)
        .eq("member_id", member_id)
        .execute()
    )
    return len(result.data) > 0


def refresh_coupons(tracked_id: str):
    """Busca cupons candidatos e verifica os elegiveis. Chamado apos criar o produto e no ciclo do scheduler."""
    sb = _supabase()

    product = sb.table("tracked_products").select("id, title").eq("id", tracked_id).single().execute().data
    if not product:
        return

    offers = sb.table("tracked_product_offers").select("marketplace, url").eq("tracked_product_id", tracked_id).execute().data

    for offer in offers:
        marketplace = offer["marketplace"]
        candidates  = find_candidates(product["title"], marketplace)

        for cand in candidates:
            existing = (
                sb.table("tracked_product_coupons")
                .select("verified, last_verified_at")
                .eq("tracked_product_id", tracked_id)
                .eq("marketplace", marketplace)
                .eq("code", cand["code"])
                .execute()
            ).data

            needs_verify = True
            if existing:
                last = existing[0].get("last_verified_at")
                if last and existing[0].get("verified") is not None:
                    age = datetime.now() - datetime.fromisoformat(last)
                    needs_verify = age > timedelta(days=RECHECK_VERIFIED_AFTER_DAYS)

            row = {
                "tracked_product_id": tracked_id,
                "marketplace":        marketplace,
                "code":               cand["code"],
                "description":        cand["description"],
                "source":             cand["source"],
            }

            if needs_verify:
                result = verify(marketplace, cand["code"], offer["url"])
                row["verified"]         = result
                row["last_verified_at"] = datetime.now().isoformat()

            sb.table("tracked_product_coupons").upsert(
                row, on_conflict="tracked_product_id,marketplace,code"
            ).execute()
```

- [ ] **Step 4: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_tracked_product_service.py -v`
Expected: `PASS` (6 testes)

- [ ] **Step 5: Commit**

```bash
git add clubeusa/services/tracked_product_service.py clubeusa/tests/test_tracked_product_service.py
git commit -m "feat(services): adicionar tracked_product_service (orquestracao + persistencia)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Endpoints da API — `/products/track*` e `PATCH /member/profile`

**Files:**
- Modify: `clubeusa/api/main.py`
- Test: `clubeusa/tests/test_api_products_track.py`

**Interfaces:**
- Consumes: `services.tracked_product_service.*` (Task 6), `deps.require_paid_plan`/`get_current_member` (já existentes)
- Produces: rotas HTTP consumidas pelo frontend na Task 9

- [ ] **Step 1: Escrever os testes que falham**

```python
# clubeusa/tests/test_api_products_track.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

def _client_with_paid_member(mocker):
    from main import app
    import deps
    app.dependency_overrides[deps.require_paid_plan] = lambda: {"sub": "m-1", "plan": "vip"}
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-1", "plan": "vip"}
    return TestClient(app)

def test_post_products_track_returns_201(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.create_tracked_product",
        return_value={"id": "tp-1", "title": "Echo Dot", "offers": []},
    )
    resp = client.post("/products/track", json={"url": "https://www.amazon.com/dp/B08N5WRWNW"})
    assert resp.status_code == 201
    assert resp.json()["id"] == "tp-1"

def test_post_products_track_returns_400_on_value_error(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.create_tracked_product",
        side_effect=ValueError("Link não reconhecido."),
    )
    resp = client.post("/products/track", json={"url": "https://google.com"})
    assert resp.status_code == 400

def test_get_products_track_lists_member_products(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.list_tracked_products",
        return_value=[{"id": "tp-1", "title": "Echo Dot"}],
    )
    resp = client.get("/products/track")
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "tp-1"

def test_delete_products_track_returns_204(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch("services.tracked_product_service.cancel_tracked_product", return_value=True)
    resp = client.delete("/products/track/tp-1")
    assert resp.status_code == 204

def test_delete_products_track_returns_404_when_not_found(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch("services.tracked_product_service.cancel_tracked_product", return_value=False)
    resp = client.delete("/products/track/tp-inexistente")
    assert resp.status_code == 404
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_api_products_track.py -v`
Expected: `FAIL` — `404 Not Found` nas rotas (ainda não existem)

- [ ] **Step 3: Adicionar os schemas e as rotas em `api/main.py`**

Adicionar perto de `class AlertFromLink` (por volta da linha 210):

```python
class TrackProductRequest(BaseModel):
    url: str
```

Adicionar perto das rotas `/alerts/*` (por volta da linha 883, após `create_alert_from_link`):

```python
@app.post("/products/track", status_code=201)
async def track_product(body: TrackProductRequest, member: dict = Depends(require_paid_plan)):
    """Rastreia um produto: identifica a fonte, busca ofertas cruzadas e dispara verificacao de cupons."""
    from services.tracked_product_service import create_tracked_product
    try:
        return create_tracked_product(member["sub"], body.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/products/track")
async def list_tracked_products_route(member: dict = Depends(require_paid_plan)):
    """Lista produtos rastreados do membro, com ofertas e cupons."""
    from services.tracked_product_service import list_tracked_products
    return list_tracked_products(member["sub"])


@app.get("/products/track/{tracked_id}")
async def get_tracked_product_route(tracked_id: str, member: dict = Depends(require_paid_plan)):
    """Detalhe de um produto rastreado."""
    from services.tracked_product_service import get_tracked_product
    result = get_tracked_product(tracked_id, member["sub"])
    if not result:
        raise HTTPException(status_code=404, detail="Produto rastreado não encontrado.")
    return result


@app.delete("/products/track/{tracked_id}", status_code=204)
async def cancel_tracked_product_route(tracked_id: str, member: dict = Depends(require_paid_plan)):
    """Cancela o rastreamento de um produto."""
    from services.tracked_product_service import cancel_tracked_product
    found = cancel_tracked_product(tracked_id, member["sub"])
    if not found:
        raise HTTPException(status_code=404, detail="Produto rastreado não encontrado.")
```

Adicionar `PATCH /member/profile` perto de `GET /member/profile` (por volta da linha 387):

```python
class UpdateCategoriesRequest(BaseModel):
    categories: list[str]

    @field_validator("categories")
    @classmethod
    def validate_categories(cls, v):
        valid = {"all","electronics","kitchen","baby","fitness",
                 "beauty","tools","pets","fashion","automotive","books"}
        cleaned = [c for c in v if c in valid]
        return cleaned or ["all"]


@app.patch("/member/profile")
async def update_profile_categories(body: UpdateCategoriesRequest, member: dict = Depends(get_current_member)):
    """Atualiza os nichos (categorias) de interesse do membro."""
    from services.member_service import update_member_categories
    return update_member_categories(member["sub"], body.categories)
```

- [ ] **Step 4: Adicionar `update_member_categories` em `services/member_service.py`**

```python
def update_member_categories(member_id: str, categories: list) -> dict:
    sb = _supabase()
    result = sb.table("members").update({"categories": categories}).eq("id", member_id).execute()
    if not result.data:
        raise ValueError("Membro não encontrado.")
    return {"categories": result.data[0]["categories"]}
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_api_products_track.py -v`
Expected: `PASS` (5 testes)

- [ ] **Step 6: Rodar a suíte completa**

Run: `cd clubeusa && python -m pytest tests/ -v`
Expected: todos os testes `PASS`

- [ ] **Step 7: Commit**

```bash
git add clubeusa/api/main.py clubeusa/services/member_service.py clubeusa/tests/test_api_products_track.py
git commit -m "feat(api): adicionar endpoints /products/track* e PATCH /member/profile

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 8: `scheduler.py` — ciclo de recheck a cada 6h

**Files:**
- Modify: `dealscanner2/scheduler.py`
- Test: `clubeusa/tests/test_scheduler_tracked_products.py`

**Interfaces:**
- Consumes: `services.tracked_product_service.list_tracked_products` não é usado aqui — o scheduler consulta o Supabase diretamente (mesmo padrão de `alert_checker.check_price_alerts`), e chama `product_matcher.fetch_source_details`/`find_offers` e `services.tracked_product_service.refresh_coupons`
- Produces: `check_tracked_products()`, adicionado ao dispatch de `run_loop()` e à `build_event_queue()`

- [ ] **Step 1: Escrever o teste que falha**

```python
# clubeusa/tests/test_scheduler_tracked_products.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock

def test_check_tracked_products_updates_price_and_refreshes_coupons(mocker):
    from scheduler import check_tracked_products

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "tp-1", "title": "Echo Dot", "source": "amazon", "source_id": "B08N5WRWNW"},
    ]
    mocker.patch("scheduler._supabase", return_value=mock_sb)
    mocker.patch(
        "scheduler.fetch_source_details",
        return_value={"title": "Echo Dot", "price": 19.99, "image_url": None, "url": "https://amazon.com/dp/B08N5WRWNW"},
    )
    mocker.patch("scheduler.find_offers", return_value=[])
    mock_refresh = mocker.patch("scheduler.refresh_coupons")

    check_tracked_products()

    mock_refresh.assert_called_once_with("tp-1")
    mock_sb.table().upsert.assert_called()

def test_check_tracked_products_skips_product_on_error(mocker):
    from scheduler import check_tracked_products

    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": "tp-1", "title": "Echo Dot", "source": "amazon", "source_id": "B08N5WRWNW"},
        {"id": "tp-2", "title": "Air Fryer", "source": "walmart", "source_id": "114215867"},
    ]
    mocker.patch("scheduler._supabase", return_value=mock_sb)
    mocker.patch("scheduler.fetch_source_details", side_effect=[Exception("API fora do ar"), {
        "title": "Air Fryer", "price": 59.0, "image_url": None, "url": "https://walmart.com/ip/1",
    }])
    mocker.patch("scheduler.find_offers", return_value=[])
    mock_refresh = mocker.patch("scheduler.refresh_coupons")

    check_tracked_products()

    # tp-1 falhou mas tp-2 ainda deve ter sido processado
    mock_refresh.assert_called_once_with("tp-2")
```

- [ ] **Step 2: Rodar os testes e confirmar que falham**

Run: `cd clubeusa && python -m pytest tests/test_scheduler_tracked_products.py -v`
Expected: `FAIL` — `ImportError: cannot import name 'check_tracked_products'`

- [ ] **Step 3: Adicionar `check_tracked_products` ao `scheduler.py`**

Adicionar os imports no topo do arquivo (perto da linha 32):

```python
from product_matcher import fetch_source_details, find_offers
from services.tracked_product_service import refresh_coupons
```

Adicionar a função `_supabase()` (se ainda não existir uma reaproveitável no arquivo — usar a mesma da `alert_checker.py`) e a função principal, antes de `run_loop()`:

```python
def _supabase():
    from supabase import create_client
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


def check_tracked_products():
    """Reconsulta preco de todos os produtos rastreados ativos e atualiza cupons."""
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        log.warning("Supabase não configurado — rastreamento de produtos ignorado.")
        return

    sb = _supabase()
    products = sb.table("tracked_products").select("*").eq("status", "active").execute().data
    if not products:
        log.info("Nenhum produto rastreado ativo.")
        return

    log.info(f"Verificando {len(products)} produtos rastreados...")

    for product in products:
        try:
            details = fetch_source_details(product["source"], product["source_id"])
            sb.table("tracked_product_offers").upsert({
                "tracked_product_id": product["id"],
                "marketplace":        product["source"],
                "price":              details["price"],
                "url":                details["url"],
            }, on_conflict="tracked_product_id,marketplace").execute()

            for offer in find_offers(details["title"], exclude_source=product["source"]):
                sb.table("tracked_product_offers").upsert({
                    "tracked_product_id": product["id"],
                    "marketplace":        offer["marketplace"],
                    "price":              offer["price"],
                    "url":                offer["url"],
                }, on_conflict="tracked_product_id,marketplace").execute()

            refresh_coupons(product["id"])

        except Exception as e:
            log.error(f"Erro ao verificar produto rastreado {product['id']}: {e}")
            continue

    log.info("Verificação de produtos rastreados concluída.")
```

- [ ] **Step 4: Adicionar o evento de recheck à fila (`build_event_queue`) e ao dispatch (`run_loop`)**

Em `build_event_queue()`, adicionar (perto do bloco de `news_fetch`, por volta da linha 553):

```python
    # Recheck de produtos rastreados a cada 6h (UTC 2, 8, 14, 20)
    for tp_hour in [2, 8, 14, 20]:
        events.append({
            "utc_hour": tp_hour,
            "type":     "tracked_products_check",
            "slot":     None,
            "tz":       "eastern",
            "plan":     None,
            "secs":     seconds_until_utc(tp_hour),
        })
```

Em `run_loop()`, adicionar ao bloco `if/elif` de dispatch (por volta da linha 628):

```python
        elif next_e["type"] == "tracked_products_check":
            check_tracked_products()
```

- [ ] **Step 5: Rodar os testes e confirmar que passam**

Run: `cd clubeusa && python -m pytest tests/test_scheduler_tracked_products.py -v`
Expected: `PASS` (2 testes)

- [ ] **Step 6: Rodar a suíte completa**

Run: `cd clubeusa && python -m pytest tests/ -v`
Expected: todos os testes `PASS`

- [ ] **Step 7: Commit**

```bash
git add dealscanner2/scheduler.py clubeusa/tests/test_scheduler_tracked_products.py
git commit -m "feat(scheduler): adicionar ciclo de recheck de produtos rastreados a cada 6h

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 9: `sender.py` — notificação de queda de preço/cupom confirmado

**Files:**
- Modify: `dealscanner2/sender.py`
- Test: `clubeusa/tests/test_sender_tracked_product.py`

**Interfaces:**
- Consumes: `_send_message`/`_send_whatsapp` (já existentes no mesmo arquivo)
- Produces: `send_tracked_product_alert(product: dict, offer: dict, coupon: dict | None, phone: str, lang: str = "pt")`, usado pela Task 8 quando quiser notificar (chamada adicionada manualmente por quem mantiver — a task cobre a função em si; o gatilho de notificação fica marcado como próximo passo natural do `check_tracked_products`, mas não é obrigatório para o produto funcionar: a UI já mostra os dados atualizados)

- [ ] **Step 1: Escrever o teste que falha**

```python
# clubeusa/tests/test_sender_tracked_product.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dealscanner2'))

def test_send_tracked_product_alert_includes_coupon_when_verified(mocker):
    from sender import send_tracked_product_alert

    mock_send = mocker.patch("sender._send_message")

    product = {"title": "Echo Dot (4th Gen)"}
    offer   = {"marketplace": "amazon", "price": 18.39, "url": "https://amazon.com/dp/B08N5WRWNW"}
    coupon  = {"code": "SAVE20ECHO", "verified": True}

    send_tracked_product_alert(product, offer, coupon, phone="+15551234567", lang="pt")

    mock_send.assert_called_once()
    sent_text = mock_send.call_args[0][1]
    assert "SAVE20ECHO" in sent_text
    assert "Echo Dot" in sent_text

def test_send_tracked_product_alert_omits_coupon_when_none(mocker):
    from sender import send_tracked_product_alert

    mock_send = mocker.patch("sender._send_message")

    product = {"title": "Echo Dot (4th Gen)"}
    offer   = {"marketplace": "amazon", "price": 18.39, "url": "https://amazon.com/dp/B08N5WRWNW"}

    send_tracked_product_alert(product, offer, None, phone="+15551234567", lang="pt")

    sent_text = mock_send.call_args[0][1]
    assert "Cupom" not in sent_text
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd clubeusa && python -m pytest tests/test_sender_tracked_product.py -v`
Expected: `FAIL` — `ImportError: cannot import name 'send_tracked_product_alert'`

- [ ] **Step 3: Implementar `send_tracked_product_alert` em `sender.py`**

```python
def send_tracked_product_alert(product: dict, offer: dict, coupon: dict | None, phone: str, lang: str = "pt") -> None:
    """Notifica o membro sobre queda de preco (e cupom confirmado, se houver) de um produto rastreado."""
    if lang == "es":
        lines = [
            "💰 *Bajada de precio — Club USA*", "",
            f"*{product['title'][:80]}*",
            f"{offer['marketplace'].title()}: *${offer['price']:.2f}*",
        ]
    else:
        lines = [
            "💰 *Queda de preço — Clube USA*", "",
            f"*{product['title'][:80]}*",
            f"{offer['marketplace'].title()}: *${offer['price']:.2f}*",
        ]

    if coupon and coupon.get("verified"):
        label = "Cupom confirmado" if lang != "es" else "Cupón confirmado"
        lines.append(f"🎟️ {label}: `{coupon['code']}`")

    lines += ["", offer["url"]]
    message = "\n".join(lines)

    _send_message(phone, message)
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd clubeusa && python -m pytest tests/test_sender_tracked_product.py -v`
Expected: `PASS` (2 testes)

- [ ] **Step 5: Rodar a suíte completa do projeto**

Run: `cd clubeusa && python -m pytest tests/ -v`
Expected: todos os testes `PASS`

- [ ] **Step 6: Commit**

```bash
git add dealscanner2/sender.py clubeusa/tests/test_sender_tracked_product.py
git commit -m "feat(sender): adicionar notificacao de produto rastreado com cupom confirmado

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 10: UI em `platform.html` — nichos, adicionar produto, meus produtos

**Files:**
- Modify: `clubeusa/platform.html`

**Interfaces:**
- Consumes: `PATCH /member/profile`, `POST /products/track`, `GET /products/track`, `GET /products/track/{id}`, `DELETE /products/track/{id}` (Task 7)

Esta task é de frontend (HTML/JS embutido, seguindo o padrão já usado em `platform.html` para as demais telas do painel) — não tem ciclo de teste automatizado; a verificação é manual, listada no Step final.

- [ ] **Step 1: Localizar a seção de perfil existente em `platform.html`**

Run: `grep -n "member/profile\|categories" clubeusa/platform.html`

Usar essa seção como referência de estilo (classes CSS, padrão de fetch com `Authorization: Bearer`) para as três telas novas.

- [ ] **Step 2: Adicionar a seção "Meus Nichos" na tela de perfil**

Checkboxes para cada categoria válida (`electronics, kitchen, baby, fitness, beauty, tools, pets, fashion, automotive, books`), pré-marcados com `member.categories` (já retornado por `GET /member/profile`). Botão "Salvar" chama:

```js
async function saveCategories(selected) {
  const res = await fetch('/member/profile', {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ categories: selected }),
  });
  if (!res.ok) throw new Error('Falha ao salvar nichos');
  return res.json();
}
```

- [ ] **Step 3: Adicionar a seção "Adicionar Produto"**

Campo de texto + botão. Ao submeter:

```js
async function trackProduct(url) {
  const res = await fetch('/products/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Não foi possível rastrear este produto.');
  }
  return res.json();
}
```

Renderizar a resposta: lista de ofertas ordenada por `price` crescente, e um placeholder "Verificando cupons..." que faz polling em `GET /products/track/{id}` a cada 5s (até 3 tentativas) para atualizar a lista de cupons quando `coupons` deixar de estar vazia ou passar 15s (timeout de exibição, mostrando "nenhum cupom encontrado" se nada vier).

Cada cupom renderiza:
- `verified === true` → selo verde "✓ cupom confirmado" + código copiável
- `verified === false` ou `null` → selo cinza "cupom não confirmado — pode não estar mais ativo"

- [ ] **Step 4: Adicionar a seção "Meus Produtos"**

```js
async function loadTrackedProducts() {
  const res = await fetch('/products/track', {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
}

async function removeTrackedProduct(id) {
  await fetch(`/products/track/${id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });
}
```

Cada card mostra título, imagem (se houver), preço mais barato encontrado, badge "marketplace" da oferta mais barata, e botão "Remover".

- [ ] **Step 5: Teste manual end-to-end**

Rodar a API localmente (`cd clubeusa/api && uvicorn main:app --reload`), logar como membro com plano pago, e verificar manualmente:
1. Editar nichos no perfil e confirmar que persistem após reload
2. Colar um link de produto Amazon válido e confirmar que aparecem ofertas de outros marketplaces
3. Confirmar que cupons aparecem com o selo correto (confirmado ou não confirmado)
4. Remover um produto rastreado e confirmar que some da lista

- [ ] **Step 6: Commit**

```bash
git add clubeusa/platform.html
git commit -m "feat(ui): adicionar telas de nichos, rastrear produto e meus produtos

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Pós-implementação (fora deste plano, não bloqueante)

- Rodar `product_tracker_migration.sql` manualmente no Supabase SQL Editor (Task 1) antes de fazer deploy das tasks 6-8 em produção
- Rodar `playwright install chromium` no ambiente do Render (adicionar ao `buildCommand` do `render.yaml` quando for fazer deploy: `pip install -r requirements.txt && playwright install --with-deps chromium`)
- Driver de verificação para Walmart/BestBuy (deferido — v1 os retorna como "não verificável", conforme Global Constraints)
- Suporte a Target (deferido — sem API de busca por produto disponível hoje)
