"""Testes de integração das rotas de promoções — DB mockado."""
from unittest.mock import MagicMock

import pytest

ADMIN_HEADER = {"X-Admin-Key": "test-admin-key-for-unit-tests"}

_BASE_PROMO = {
    "id": "promo-123",
    "title": "10% off em todo o mercado",
    "description": "Desconto válido em qualquer compra acima de $20.",
    "url": "https://example.com/oferta",
    "image_url": None,
    "category": "supermercado",
    "zip_code": None,
    "state": "FL",
    "expires_at": None,
    "is_featured": False,
    "is_active": True,
    "created_at": "2026-07-01T00:00:00+00:00",
}


def _set_list(mock_db, data):
    """Configura a cadeia .select().eq().order().order().limit().execute()"""
    (
        mock_db.table.return_value
        .select.return_value
        .eq.return_value
        .order.return_value
        .order.return_value
        .limit.return_value
        .execute.return_value.data
    ) = data


def _set_single(mock_db, data):
    """Configura a cadeia .select().eq().eq().execute() (busca por id + is_active)"""
    (
        mock_db.table.return_value
        .select.return_value
        .eq.return_value
        .eq.return_value
        .execute.return_value.data
    ) = data


def _set_insert(mock_db, data):
    mock_db.table.return_value.insert.return_value.execute.return_value.data = data


def _set_admin_list(mock_db, data):
    """Configura .select().order().execute() (admin list sem filtro is_active)"""
    (
        mock_db.table.return_value
        .select.return_value
        .order.return_value
        .execute.return_value.data
    ) = data


def _set_update_then_select(mock_db, select_data):
    """update().eq().execute() + select().eq().execute() para update_promotion."""
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = select_data


# ─── GET /api/promotions ──────────────────────────────────────────────────────

class TestListPromotions:
    def test_returns_active_promotions(self, client, mock_db):
        _set_list(mock_db, [_BASE_PROMO])

        r = client.get("/api/promotions")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == "promo-123"
        assert data["items"][0]["is_urgent"] is False

    def test_no_auth_required(self, client, mock_db):
        _set_list(mock_db, [])
        # Sem token → ainda retorna 200 (rota pública)
        r = client.get("/api/promotions")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_filters_expired_promotions(self, client, mock_db):
        expired = {**_BASE_PROMO, "expires_at": "2020-01-01T00:00:00+00:00"}
        _set_list(mock_db, [expired])

        r = client.get("/api/promotions")
        assert r.status_code == 200
        # Promoção expirada deve ser filtrada
        assert r.json()["total"] == 0

    def test_urgent_flag_set_correctly(self, client, mock_db):
        from datetime import datetime, timedelta, timezone

        soon = (datetime.now(timezone.utc) + timedelta(hours=12)).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00"
        )
        urgent_promo = {**_BASE_PROMO, "expires_at": soon}
        _set_list(mock_db, [urgent_promo])

        r = client.get("/api/promotions")
        assert r.status_code == 200
        assert r.json()["items"][0]["is_urgent"] is True

    def test_filter_by_category(self, client, mock_db):
        restaurante = {**_BASE_PROMO, "id": "p2", "category": "restaurante"}
        _set_list(mock_db, [_BASE_PROMO, restaurante])

        r = client.get("/api/promotions?category=restaurante")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 1
        assert data["items"][0]["category"] == "restaurante"

    def test_filter_by_state_includes_national(self, client, mock_db):
        national = {**_BASE_PROMO, "id": "p_nat", "state": None}
        fl_promo = {**_BASE_PROMO, "id": "p_fl", "state": "FL"}
        tx_promo = {**_BASE_PROMO, "id": "p_tx", "state": "TX"}
        _set_list(mock_db, [national, fl_promo, tx_promo])

        r = client.get("/api/promotions?state=FL")
        assert r.status_code == 200
        ids = {i["id"] for i in r.json()["items"]}
        assert "p_nat" in ids  # nacional aparece sempre
        assert "p_fl" in ids
        assert "p_tx" not in ids


# ─── GET /api/promotions/{id} ─────────────────────────────────────────────────

class TestGetPromotion:
    def test_success(self, client, mock_db):
        _set_single(mock_db, [_BASE_PROMO])

        r = client.get("/api/promotions/promo-123")
        assert r.status_code == 200
        assert r.json()["id"] == "promo-123"

    def test_not_found_returns_404(self, client, mock_db):
        _set_single(mock_db, [])

        r = client.get("/api/promotions/nao-existe")
        assert r.status_code == 404


# ─── POST /api/promotions/{id}/click ─────────────────────────────────────────

class TestTrackClick:
    def test_success(self, client, mock_db):
        _set_single(mock_db, [{"id": "promo-123"}])
        mock_db.table.return_value.insert.return_value.execute.return_value.data = []

        r = client.post("/api/promotions/promo-123/click")
        assert r.status_code == 200
        assert r.json()["message"] == "ok"

    def test_not_found_returns_404(self, client, mock_db):
        _set_single(mock_db, [])

        r = client.post("/api/promotions/nao-existe/click")
        assert r.status_code == 404


# ─── POST /api/admin/promotions ───────────────────────────────────────────────

class TestAdminCreatePromotion:
    _VALID_BODY = {
        "title": "Grande promoção",
        "description": "Economize já",
        "url": "https://example.com/deal",
        "category": "supermercado",
    }

    def test_success(self, client, mock_db):
        created = {**_BASE_PROMO, "title": "Grande promoção"}
        _set_insert(mock_db, [created])

        r = client.post("/api/admin/promotions", json=self._VALID_BODY, headers=ADMIN_HEADER)
        assert r.status_code == 201
        assert r.json()["title"] == "Grande promoção"

    def test_no_admin_key_returns_403(self, client, mock_db):
        r = client.post("/api/admin/promotions", json=self._VALID_BODY)
        assert r.status_code == 403

    def test_wrong_admin_key_returns_403(self, client, mock_db):
        r = client.post(
            "/api/admin/promotions",
            json=self._VALID_BODY,
            headers={"X-Admin-Key": "chave-errada"},
        )
        assert r.status_code == 403

    def test_blank_title_rejected(self, client, mock_db):
        body = {**self._VALID_BODY, "title": "   "}
        r = client.post("/api/admin/promotions", json=body, headers=ADMIN_HEADER)
        assert r.status_code == 422

    def test_invalid_category_rejected(self, client, mock_db):
        body = {**self._VALID_BODY, "category": "invalid-category"}
        r = client.post("/api/admin/promotions", json=body, headers=ADMIN_HEADER)
        assert r.status_code == 422


# ─── GET /api/admin/promotions ────────────────────────────────────────────────

class TestAdminListPromotions:
    def test_success(self, client, mock_db):
        inactive = {**_BASE_PROMO, "id": "p2", "is_active": False}
        _set_admin_list(mock_db, [_BASE_PROMO, inactive])

        r = client.get("/api/admin/promotions", headers=ADMIN_HEADER)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2  # inclui inativas

    def test_no_admin_key_returns_403(self, client, mock_db):
        r = client.get("/api/admin/promotions")
        assert r.status_code == 403


# ─── PUT /api/admin/promotions/{id} ──────────────────────────────────────────

class TestAdminUpdatePromotion:
    def test_update_title(self, client, mock_db):
        updated = {**_BASE_PROMO, "title": "Novo título"}
        _set_update_then_select(mock_db, [updated])

        r = client.put(
            "/api/admin/promotions/promo-123",
            json={"title": "Novo título"},
            headers=ADMIN_HEADER,
        )
        assert r.status_code == 200
        assert r.json()["title"] == "Novo título"

    def test_no_admin_key_returns_403(self, client, mock_db):
        r = client.put("/api/admin/promotions/promo-123", json={"title": "x"})
        assert r.status_code == 403

    def test_not_found_returns_404(self, client, mock_db):
        _set_update_then_select(mock_db, [])

        r = client.put(
            "/api/admin/promotions/nao-existe",
            json={"title": "Novo título"},
            headers=ADMIN_HEADER,
        )
        assert r.status_code == 404


# ─── DELETE /api/admin/promotions/{id} ───────────────────────────────────────

class TestAdminDeletePromotion:
    def test_success(self, client, mock_db):
        mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []

        r = client.delete("/api/admin/promotions/promo-123", headers=ADMIN_HEADER)
        assert r.status_code == 200
        assert "desativada" in r.json()["message"].lower()

    def test_no_admin_key_returns_403(self, client, mock_db):
        r = client.delete("/api/admin/promotions/promo-123")
        assert r.status_code == 403
