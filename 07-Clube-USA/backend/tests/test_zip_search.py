"""
Testes para Fase 1.2 — Busca por ZIP + raio.

Cobre:
- Haversine (unidade)
- search_promotions_by_zip (service, com mock Supabase)
- GET /promotions?zip=XXXXX (API)
- GET /promotions/search?zip=XXXXX (API)
- ZIP desconhecido -> 422
- Promoções além do raio excluídas
- Promoções nacionais (sem lat/lng) sempre inclusas
- Paginação no resultado filtrado
"""
import pytest

from geo.haversine import haversine_miles


# ---------------------------------------------------------------------------
# Haversine — unidade pura, sem rede
# ---------------------------------------------------------------------------


class TestHaversine:
    def test_same_point_is_zero(self):
        assert haversine_miles(25.7617, -80.1918, 25.7617, -80.1918) == pytest.approx(0, abs=0.001)

    def test_miami_to_miami_beach_approx_5_miles(self):
        # Distância real entre centro de Miami e Miami Beach: ~5-6 milhas
        dist = haversine_miles(25.7617, -80.1918, 25.7882, -80.1339)
        assert 4.0 < dist < 7.0, f"Esperado 4-7 mi, obtido {dist:.2f}"

    def test_miami_to_orlando_approx_235_miles(self):
        dist = haversine_miles(25.7617, -80.1918, 28.5383, -81.3792)
        assert 220 < dist < 250, f"Esperado ~235 mi, obtido {dist:.2f}"

    def test_symmetric(self):
        d1 = haversine_miles(40.7128, -74.0060, 42.3601, -71.0589)
        d2 = haversine_miles(42.3601, -71.0589, 40.7128, -74.0060)
        assert d1 == pytest.approx(d2, rel=1e-6)

    def test_new_york_to_boston_approx_190_miles(self):
        dist = haversine_miles(40.7128, -74.0060, 42.3601, -71.0589)
        assert 180 < dist < 210, f"Esperado ~190 mi, obtido {dist:.2f}"


# ---------------------------------------------------------------------------
# Helpers de mock
# ---------------------------------------------------------------------------

PROMO_NATIONAL = {
    "id": "national-1",
    "title": "Oferta Nacional",
    "description": "Para todos os estados",
    "store": "Amazon",
    "category": "compras",
    "zip_code": None,
    "latitude": None,
    "longitude": None,
    "expires_at": None,
    "discount_url": None,
    "discount_code": None,
    "image_url": None,
    "active": True,
    "created_at": "2026-07-01T10:00:00Z",
    "updated_at": "2026-07-01T10:00:00Z",
}

PROMO_MIAMI_CLOSE = {
    "id": "miami-close-1",
    "title": "Cafézinho Brickell",
    "description": "2x1 no café",
    "store": "Café Brasil",
    "category": "alimentacao",
    "zip_code": "33130",
    "latitude": 25.7617,   # Miami Downtown — perto da busca
    "longitude": -80.1918,
    "expires_at": None,
    "discount_url": None,
    "discount_code": None,
    "image_url": None,
    "active": True,
    "created_at": "2026-07-02T10:00:00Z",
    "updated_at": "2026-07-02T10:00:00Z",
}

PROMO_ORLANDO_FAR = {
    "id": "orlando-1",
    "title": "Promoção Orlando",
    "description": "Apenas em Orlando",
    "store": "Loja Orlando",
    "category": "compras",
    "zip_code": "32801",
    "latitude": 28.5383,  # Orlando — fora do raio de Miami
    "longitude": -81.3792,
    "expires_at": None,
    "discount_url": None,
    "discount_code": None,
    "image_url": None,
    "active": True,
    "created_at": "2026-07-03T10:00:00Z",
    "updated_at": "2026-07-03T10:00:00Z",
}

ZIP_33130_ROW = {"latitude": 25.7617, "longitude": -80.1918}


def _setup_zip_lookup(mock_supabase, zip_data):
    """Configura mock para lookup de zip_codes."""
    zip_chain = (
        mock_supabase.table.return_value
        .select.return_value
        .eq.return_value
        .maybe_single.return_value
    )
    zip_chain.execute.return_value.data = zip_data


def _setup_promo_list(mock_supabase, rows):
    """Configura mock para .select("*").eq(...).or_(...).execute()."""
    promo_chain = (
        mock_supabase.table.return_value
        .select.return_value
        .eq.return_value
        .or_.return_value
    )
    promo_chain.execute.return_value.data = rows


# ---------------------------------------------------------------------------
# Service — search_promotions_by_zip
# ---------------------------------------------------------------------------


class TestSearchByZip:
    def test_unknown_zip_raises_value_error(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, None)
        from promotions.service import search_promotions_by_zip
        with pytest.raises(ValueError, match="não encontrado"):
            search_promotions_by_zip(mock_supabase, "99999", radius_miles=5)

    def test_national_promo_always_included(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [PROMO_NATIONAL])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5)
        assert result.total == 1
        assert result.items[0].id == "national-1"
        assert result.items[0].distance_miles is None

    def test_local_promo_within_radius_included(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [PROMO_MIAMI_CLOSE])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5)
        assert result.total == 1
        assert result.items[0].id == "miami-close-1"
        assert result.items[0].distance_miles is not None
        assert result.items[0].distance_miles < 5

    def test_promo_beyond_radius_excluded(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [PROMO_ORLANDO_FAR])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5)
        assert result.total == 0

    def test_local_before_national_in_results(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [PROMO_NATIONAL, PROMO_MIAMI_CLOSE])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=10)
        assert result.items[0].id == "miami-close-1"  # local primeiro
        assert result.items[1].id == "national-1"

    def test_mixed_results_correct_total(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [PROMO_NATIONAL, PROMO_MIAMI_CLOSE, PROMO_ORLANDO_FAR])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5)
        # Orlando (>200mi) excluído; nacional + miami incluídos = 2
        assert result.total == 2
        ids = [r.id for r in result.items]
        assert "orlando-1" not in ids

    def test_pagination(self, mock_supabase):
        rows = [
            {**PROMO_NATIONAL, "id": f"nat-{i}", "created_at": f"2026-07-0{i}T00:00:00Z"}
            for i in range(1, 6)
        ]
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, rows)
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5, page=1, page_size=3)
        assert result.total == 5
        assert len(result.items) == 3
        assert result.has_more is True

        result_p2 = search_promotions_by_zip(mock_supabase, "33130", radius_miles=5, page=2, page_size=3)
        assert len(result_p2.items) == 2
        assert result_p2.has_more is False

    def test_result_contains_search_metadata(self, mock_supabase):
        _setup_zip_lookup(mock_supabase, ZIP_33130_ROW)
        _setup_promo_list(mock_supabase, [])
        from promotions.service import search_promotions_by_zip
        result = search_promotions_by_zip(mock_supabase, "33130", radius_miles=3)
        assert result.search_zip == "33130"
        assert result.radius_miles == 3


# ---------------------------------------------------------------------------
# API — GET /promotions (com e sem ZIP)
# ---------------------------------------------------------------------------


class TestListPromotionsApiZip:
    def test_without_zip_returns_normal_list(self, client, mock_supabase):
        chain = (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .or_.return_value
            .order.return_value
            .range.return_value
        )
        chain.execute.return_value.data = []
        chain.execute.return_value.count = 0
        resp = client.get("/promotions")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_with_valid_zip_returns_search_result(self, client, mock_supabase):
        # Mock: zip lookup encontrado
        (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ).data = ZIP_33130_ROW
        # Mock: promos
        (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .or_.return_value
            .execute.return_value
        ).data = [PROMO_NATIONAL]

        resp = client.get("/promotions?zip=33130&radius=5")
        assert resp.status_code == 200
        body = resp.json()
        assert "search_zip" in body
        assert body["search_zip"] == "33130"

    def test_with_unknown_zip_returns_422(self, client, mock_supabase):
        (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ).data = None
        resp = client.get("/promotions?zip=99999")
        assert resp.status_code == 422

    def test_zip_must_be_5_digits(self, client, mock_supabase):
        resp = client.get("/promotions?zip=123")
        assert resp.status_code == 422

    def test_radius_max_50(self, client, mock_supabase):
        resp = client.get("/promotions?zip=33130&radius=100")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# API — GET /promotions/search
# ---------------------------------------------------------------------------


class TestSearchEndpoint:
    def test_search_endpoint_requires_zip(self, client, mock_supabase):
        resp = client.get("/promotions/search")
        assert resp.status_code == 422

    def test_search_endpoint_works(self, client, mock_supabase):
        (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .maybe_single.return_value
            .execute.return_value
        ).data = ZIP_33130_ROW
        (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .or_.return_value
            .execute.return_value
        ).data = []
        resp = client.get("/promotions/search?zip=33130")
        assert resp.status_code == 200
        body = resp.json()
        assert body["search_zip"] == "33130"
        assert body["radius_miles"] == 5.0
