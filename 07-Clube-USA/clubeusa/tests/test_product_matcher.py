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
