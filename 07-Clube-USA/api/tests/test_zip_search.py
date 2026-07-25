"""
Testes de busca por ZIP + raio — Fase 1.2

Cobre:
- Cálculo Haversine (função pura, sem mock)
- list_promotions com zip+radius: centroide conhecido
- list_promotions com zip+radius: centroide desconhecido (fallback exact match)
- Promoções nacionais (sem lat/lng) sempre aparecem
- Promoções dentro e fora do raio
- Raio inválido (clamped para MIN/MAX)
"""
import math
from unittest.mock import MagicMock

import pytest


# ─── HELPERS DE MOCK ─────────────────────────────────────────────────────────


def _make_db(zip_centroid=None, promo_data=None):
    """
    Mock DB com side_effect por tabela:
    - "zip_codes" retorna zip_centroid (ou lista vazia)
    - qualquer outra tabela retorna promo_data para a cadeia de select
    """
    mock = MagicMock()

    zip_mock = MagicMock()
    zip_mock.select.return_value.eq.return_value.execute.return_value.data = (
        [{"latitude": zip_centroid[0], "longitude": zip_centroid[1]}]
        if zip_centroid
        else []
    )

    promo_mock = MagicMock()
    (
        promo_mock
        .select.return_value
        .eq.return_value
        .order.return_value
        .order.return_value
        .limit.return_value
        .execute.return_value.data
    ) = promo_data or []

    def _side(table_name):
        return zip_mock if table_name == "zip_codes" else promo_mock

    mock.table.side_effect = _side
    return mock


_NATIONAL_PROMO = {
    "id": "nat-1",
    "title": "Promo Nacional",
    "description": "Para todo o país",
    "url": "https://example.com",
    "image_url": None,
    "category": "supermercado",
    "zip_code": None,
    "state": None,
    "expires_at": None,
    "is_featured": False,
    "is_active": True,
    "created_at": "2026-01-01T00:00:00+00:00",
    "latitude": None,
    "longitude": None,
}

# Miami, FL: 25.7749°N 80.1977°W
_MIAMI_PROMO = {
    **_NATIONAL_PROMO,
    "id": "miami-1",
    "title": "Promo Miami",
    "zip_code": "33101",
    "latitude": 25.7749,
    "longitude": -80.1977,
}

# Orlando, FL: ~240 miles from Miami
_ORLANDO_PROMO = {
    **_NATIONAL_PROMO,
    "id": "orlando-1",
    "title": "Promo Orlando",
    "zip_code": "32801",
    "latitude": 28.5383,
    "longitude": -81.3792,
}

# Fort Lauderdale, FL: ~26 miles from Miami
_FTL_PROMO = {
    **_NATIONAL_PROMO,
    "id": "ftl-1",
    "title": "Promo Fort Lauderdale",
    "zip_code": "33301",
    "latitude": 26.1224,
    "longitude": -80.1373,
}

ADMIN_HEADER = {"X-Admin-Key": "test-admin-key-for-unit-tests"}


# ─── HAVERSINE (função pura) ──────────────────────────────────────────────────


class TestHaversine:
    def test_same_point_is_zero(self):
        from geo import haversine_miles
        assert haversine_miles(25.7749, -80.1977, 25.7749, -80.1977) == pytest.approx(0.0)

    def test_miami_to_fort_lauderdale_approx_26_miles(self):
        from geo import haversine_miles
        dist = haversine_miles(25.7749, -80.1977, 26.1224, -80.1373)
        assert 24 <= dist <= 28, f"Distância Miami→FTL esperada ~26 milhas, obtida {dist:.1f}"

    def test_miami_to_orlando_approx_204_miles(self):
        from geo import haversine_miles
        dist = haversine_miles(25.7749, -80.1977, 28.5383, -81.3792)
        assert 195 <= dist <= 215, f"Distância Miami→Orlando esperada ~204 milhas, obtida {dist:.1f}"

    def test_symmetry(self):
        from geo import haversine_miles
        d1 = haversine_miles(25.7749, -80.1977, 26.1224, -80.1373)
        d2 = haversine_miles(26.1224, -80.1373, 25.7749, -80.1977)
        assert d1 == pytest.approx(d2)

    def test_north_south_positive_distance(self):
        from geo import haversine_miles
        dist = haversine_miles(0.0, 0.0, 1.0, 0.0)
        assert dist > 0


class TestClampRadius:
    def test_below_min_clamped(self):
        from geo import clamp_radius
        assert clamp_radius(0.0) == 1.0

    def test_above_max_clamped(self):
        from geo import clamp_radius
        assert clamp_radius(999.0) == 50.0

    def test_valid_value_unchanged(self):
        from geo import clamp_radius
        assert clamp_radius(5.0) == 5.0


# ─── filter_promotions_by_zip ─────────────────────────────────────────────────


class TestFilterPromotionsByZip:
    def test_centroid_known_includes_nearby(self):
        from geo import filter_promotions_by_zip
        # Buscando em Miami (33101), raio 30 milhas: FTL (~26mi) deve aparecer
        centroid = (25.7749, -80.1977)
        result = filter_promotions_by_zip(
            [_NATIONAL_PROMO, _MIAMI_PROMO, _FTL_PROMO, _ORLANDO_PROMO],
            "33101", centroid, 30.0,
        )
        ids = {p["id"] for p in result}
        assert "nat-1" in ids      # nacional sempre aparece
        assert "miami-1" in ids    # 0 milhas
        assert "ftl-1" in ids      # ~26 milhas < 30
        assert "orlando-1" not in ids  # ~240 milhas > 30

    def test_centroid_known_excludes_far(self):
        from geo import filter_promotions_by_zip
        centroid = (25.7749, -80.1977)
        result = filter_promotions_by_zip(
            [_ORLANDO_PROMO], "33101", centroid, 5.0
        )
        assert result == []

    def test_centroid_known_national_always_included(self):
        from geo import filter_promotions_by_zip
        centroid = (25.7749, -80.1977)
        result = filter_promotions_by_zip(
            [_NATIONAL_PROMO], "33101", centroid, 1.0
        )
        assert len(result) == 1
        assert result[0]["id"] == "nat-1"

    def test_centroid_unknown_fallback_exact_match(self):
        from geo import filter_promotions_by_zip
        result = filter_promotions_by_zip(
            [_NATIONAL_PROMO, _MIAMI_PROMO, _ORLANDO_PROMO],
            "33101", None, 5.0,
        )
        ids = {p["id"] for p in result}
        assert "nat-1" in ids    # nacional
        assert "miami-1" in ids  # zip_code == "33101"
        assert "orlando-1" not in ids  # zip_code "32801" != "33101"

    def test_radius_clamped_to_min(self):
        """Raio 0 é clamped para 1 milha — promoção a 0 milhas ainda aparece."""
        from geo import filter_promotions_by_zip
        centroid = (25.7749, -80.1977)
        result = filter_promotions_by_zip([_MIAMI_PROMO], "33101", centroid, 0.0)
        assert len(result) == 1

    def test_promo_with_zip_but_no_latlon_treated_as_exact_match(self):
        """Promoção legada: tem zip_code mas não tem lat/lon."""
        from geo import filter_promotions_by_zip
        legacy = {**_MIAMI_PROMO, "latitude": None, "longitude": None}
        centroid = (25.7749, -80.1977)  # centroide conhecido para o ZIP buscado

        # Legacy promo com mesmo ZIP → aparece (exact match fallback)
        result_same = filter_promotions_by_zip([legacy], "33101", centroid, 5.0)
        assert len(result_same) == 1

        # Legacy promo com ZIP diferente → não aparece
        legacy_other = {**legacy, "zip_code": "32801"}
        result_diff = filter_promotions_by_zip([legacy_other], "33101", centroid, 5.0)
        assert len(result_diff) == 0


# ─── INTEGRAÇÃO: list_promotions com zip+radius ───────────────────────────────


class TestListPromotionsZipRadius:
    def test_zip_radius_centroid_known(self, client):
        """GET /api/promotions?zip_code=33101&radius_miles=30 com centroide no banco."""
        mock_db = _make_db(
            zip_centroid=(25.7749, -80.1977),
            promo_data=[_NATIONAL_PROMO, _MIAMI_PROMO, _FTL_PROMO, _ORLANDO_PROMO],
        )
        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        r = client.get("/api/promotions?zip_code=33101&radius_miles=30")
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()["items"]}
        assert "nat-1" in ids
        assert "miami-1" in ids
        assert "ftl-1" in ids
        assert "orlando-1" not in ids

        client.app.dependency_overrides.clear()

    def test_zip_radius_centroid_unknown_fallback(self, client):
        """Se ZIP não está no banco, faz exact match e não quebra."""
        mock_db = _make_db(
            zip_centroid=None,  # ZIP não encontrado
            promo_data=[_NATIONAL_PROMO, _MIAMI_PROMO, _ORLANDO_PROMO],
        )
        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        r = client.get("/api/promotions?zip_code=33101&radius_miles=5")
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()["items"]}
        assert "nat-1" in ids
        assert "miami-1" in ids
        assert "orlando-1" not in ids

        client.app.dependency_overrides.clear()

    def test_no_zip_param_returns_all(self, client):
        """Sem zip_code, todos são retornados (comportamento original)."""
        mock_db = _make_db(promo_data=[_NATIONAL_PROMO, _MIAMI_PROMO, _ORLANDO_PROMO])
        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        r = client.get("/api/promotions")
        assert r.status_code == 200
        assert r.json()["total"] == 3

        client.app.dependency_overrides.clear()

    def test_radius_miles_default_is_5(self, client):
        """Raio padrão de 5 milhas: FTL (~26mi) não aparece, mas Miami (0mi) aparece."""
        mock_db = _make_db(
            zip_centroid=(25.7749, -80.1977),
            promo_data=[_MIAMI_PROMO, _FTL_PROMO],
        )
        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        r = client.get("/api/promotions?zip_code=33101")  # sem radius_miles → default 5
        assert r.status_code == 200
        ids = {p["id"] for p in r.json()["items"]}
        assert "miami-1" in ids
        assert "ftl-1" not in ids

        client.app.dependency_overrides.clear()


# ─── INTEGRAÇÃO: create_promotion auto-popula lat/lng ─────────────────────────


class TestAdminCreatePromotionWithGeo:
    _BODY_WITH_ZIP = {
        "title": "Promo Geo",
        "description": "Com localização",
        "url": "https://example.com",
        "category": "restaurante",
        "zip_code": "33101",
    }

    def test_create_auto_populates_latlon_when_zip_known(self, client):
        """Criar promoção com ZIP → lat/lon preenchido automaticamente do zip_codes."""
        zip_mock = MagicMock()
        zip_mock.select.return_value.eq.return_value.execute.return_value.data = [
            {"latitude": 25.7749, "longitude": -80.1977}
        ]
        promo_mock = MagicMock()
        inserted = {
            **_NATIONAL_PROMO, "id": "geo-1", "zip_code": "33101",
            "latitude": 25.7749, "longitude": -80.1977,
        }
        promo_mock.insert.return_value.execute.return_value.data = [inserted]

        mock_db = MagicMock()
        mock_db.table.side_effect = lambda t: zip_mock if t == "zip_codes" else promo_mock

        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        r = client.post("/api/admin/promotions", json=self._BODY_WITH_ZIP, headers=ADMIN_HEADER)
        assert r.status_code == 201

        # Verifica que insert foi chamado com lat/lon
        call_args = promo_mock.insert.call_args
        inserted_data = call_args[0][0] if call_args[0] else call_args[1].get("json", {})
        assert inserted_data.get("latitude") == 25.7749
        assert inserted_data.get("longitude") == -80.1977

        client.app.dependency_overrides.clear()

    def test_create_no_zip_leaves_latlon_null(self, client):
        """Criar promoção sem ZIP → lat/lon NULL (promoção nacional)."""
        promo_mock = MagicMock()
        promo_mock.insert.return_value.execute.return_value.data = [_NATIONAL_PROMO]

        mock_db = MagicMock()
        mock_db.table.side_effect = lambda t: promo_mock

        from deps import get_db
        client.app.dependency_overrides[get_db] = lambda: mock_db

        body_no_zip = {k: v for k, v in self._BODY_WITH_ZIP.items() if k != "zip_code"}
        r = client.post("/api/admin/promotions", json=body_no_zip, headers=ADMIN_HEADER)
        assert r.status_code == 201

        call_args = promo_mock.insert.call_args
        inserted_data = call_args[0][0] if call_args[0] else {}
        assert inserted_data.get("latitude") is None
        assert inserted_data.get("longitude") is None

        client.app.dependency_overrides.clear()
