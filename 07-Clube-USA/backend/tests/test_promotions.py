import pytest

from tests.conftest import make_jwt

VALID_PROMO = {
    "title": "50% off na Costco",
    "description": "Desconto especial em produtos selecionados. Válido esta semana.",
    "store": "Costco",
    "category": "compras",
}

FULL_PROMO = {
    **VALID_PROMO,
    "zip_code": "90210",
    "expires_at": "2027-12-31T23:59:59Z",
    "discount_url": "https://costco.com/deal",
    "discount_code": "BRASIL50",
    "image_url": "https://costco.com/img/deal.jpg",
}

PROMO_ROW = {
    "id": "promo-uuid-123",
    "title": "50% off na Costco",
    "description": "Desconto especial em produtos selecionados. Válido esta semana.",
    "store": "Costco",
    "category": "compras",
    "zip_code": None,
    "expires_at": None,
    "discount_url": None,
    "discount_code": None,
    "image_url": None,
    "created_at": "2026-07-07T12:00:00Z",
}

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key-12345"}


@pytest.fixture(autouse=True)
def patch_admin_key(monkeypatch):
    monkeypatch.setattr("config.settings.ADMIN_API_KEY", "test-admin-key-12345")


# ---------------------------------------------------------------------------
# Listagem pública
# ---------------------------------------------------------------------------


class TestListPromotions:
    def _setup_list_mock(self, mock_supabase, data, count):
        chain = (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .or_.return_value
            .order.return_value
            .range.return_value
        )
        chain.execute.return_value.data = data
        chain.execute.return_value.count = count

    def test_list_empty(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [], 0)
        r = client.get("/promotions")
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["has_more"] is False

    def test_list_with_items(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [PROMO_ROW], 1)
        r = client.get("/promotions")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["title"] == "50% off na Costco"
        assert body["items"][0]["store"] == "Costco"
        assert body["total"] == 1
        assert body["has_more"] is False

    def test_list_pagination_has_more(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [PROMO_ROW] * 20, 50)
        r = client.get("/promotions?page=1&page_size=20")
        assert r.status_code == 200
        body = r.json()
        assert body["has_more"] is True
        assert body["total"] == 50
        assert body["page"] == 1
        assert body["page_size"] == 20

    def test_list_second_page(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [PROMO_ROW] * 10, 30)
        r = client.get("/promotions?page=2&page_size=20")
        assert r.status_code == 200
        body = r.json()
        assert body["page"] == 2
        assert body["has_more"] is False  # offset=20, page_size=20, total=30 → 40 < 30 → False... wait
        # Actually: offset=20, offset+page_size=40, total=30 → has_more = 40 < 30 = False. Correct.

    def test_list_no_auth_required(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [], 0)
        r = client.get("/promotions")  # sem Authorization header
        assert r.status_code == 200

    def test_list_page_size_above_max_rejected(self, client, mock_supabase):
        r = client.get("/promotions?page_size=200")
        assert r.status_code == 422

    def test_list_page_zero_rejected(self, client, mock_supabase):
        r = client.get("/promotions?page=0")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Get por ID (público)
# ---------------------------------------------------------------------------


class TestGetPromotion:
    def _setup_get_mock(self, mock_supabase, data):
        chain = (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .eq.return_value
            .maybe_single.return_value
        )
        chain.execute.return_value.data = data

    def test_get_existing(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, PROMO_ROW)
        r = client.get("/promotions/promo-uuid-123")
        assert r.status_code == 200
        assert r.json()["id"] == "promo-uuid-123"
        assert r.json()["title"] == "50% off na Costco"

    def test_get_not_found(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, None)
        r = client.get("/promotions/nonexistent-id")
        assert r.status_code == 404

    def test_get_no_auth_required(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, PROMO_ROW)
        r = client.get("/promotions/promo-uuid-123")  # sem Authorization
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Criação (admin)
# ---------------------------------------------------------------------------


class TestCreatePromotion:
    def _setup_insert_mock(self, mock_supabase, row):
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [row]

    def test_create_minimal_fields(self, client, mock_supabase):
        self._setup_insert_mock(mock_supabase, {**PROMO_ROW, "id": "new-uuid"})
        r = client.post("/admin/promotions", json=VALID_PROMO, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        assert r.json()["store"] == "Costco"
        assert r.json()["category"] == "compras"

    def test_create_all_fields(self, client, mock_supabase):
        full_row = {
            **PROMO_ROW,
            "id": "new-uuid-full",
            "zip_code": "90210",
            "discount_code": "BRASIL50",
            "discount_url": "https://costco.com/deal",
            "image_url": "https://costco.com/img/deal.jpg",
        }
        self._setup_insert_mock(mock_supabase, full_row)
        r = client.post("/admin/promotions", json=FULL_PROMO, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_wrong_admin_key(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json=VALID_PROMO,
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert r.status_code == 401

    def test_create_missing_admin_key(self, client, mock_supabase):
        r = client.post("/admin/promotions", json=VALID_PROMO)
        assert r.status_code == 422

    def test_create_empty_title_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "title": "   "},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_title_too_long_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "title": "x" * 121},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_missing_title(self, client, mock_supabase):
        payload = {k: v for k, v in VALID_PROMO.items() if k != "title"}
        r = client.post("/admin/promotions", json=payload, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_invalid_category(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "category": "invalid_cat"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_zip_letters(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "zip_code": "ABCDE"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_zip_too_short(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "zip_code": "1234"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_discount_url(self, client, mock_supabase):
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "discount_url": "not-a-url"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_valid_zip_with_dash(self, client, mock_supabase):
        """ZIP com traço (90210 = 90210, mas brasileiro não usa — teste que aceita o formato sem traço)."""
        row = {**PROMO_ROW, "id": "uuid-zip", "zip_code": "90210"}
        self._setup_insert_mock(mock_supabase, row)
        r = client.post(
            "/admin/promotions",
            json={**VALID_PROMO, "zip_code": "90210"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 201

    def test_create_admin_key_not_leaked_in_response(self, client, mock_supabase):
        self._setup_insert_mock(mock_supabase, {**PROMO_ROW, "id": "uuid-leak-test"})
        r = client.post("/admin/promotions", json=VALID_PROMO, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        assert "test-admin-key-12345" not in r.text


# ---------------------------------------------------------------------------
# Desativação (admin)
# ---------------------------------------------------------------------------


class TestDeactivatePromotion:
    def _setup_deactivate_mock(self, mock_supabase, data):
        chain = (
            mock_supabase.table.return_value
            .update.return_value
            .eq.return_value
        )
        chain.execute.return_value.data = data

    def test_deactivate_success(self, client, mock_supabase):
        self._setup_deactivate_mock(mock_supabase, [{"id": "promo-uuid-123", "active": False}])
        r = client.delete("/admin/promotions/promo-uuid-123", headers=ADMIN_HEADERS)
        assert r.status_code == 204

    def test_deactivate_not_found(self, client, mock_supabase):
        self._setup_deactivate_mock(mock_supabase, [])
        r = client.delete("/admin/promotions/nonexistent", headers=ADMIN_HEADERS)
        assert r.status_code == 404

    def test_deactivate_wrong_key(self, client, mock_supabase):
        r = client.delete(
            "/admin/promotions/promo-uuid-123",
            headers={"X-Admin-Key": "wrong"},
        )
        assert r.status_code == 401

    def test_deactivate_no_key(self, client, mock_supabase):
        r = client.delete("/admin/promotions/promo-uuid-123")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Segurança: isolamento admin/usuário
# ---------------------------------------------------------------------------


class TestPromotionSecurity:
    def test_user_bearer_token_cannot_create(self, client, mock_supabase):
        """Bearer token de usuário não substitui X-Admin-Key."""
        token = make_jwt("user-123")
        r = client.post(
            "/admin/promotions",
            json=VALID_PROMO,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422  # X-Admin-Key header obrigatório ausente

    def test_admin_key_as_bearer_rejected(self, client, mock_supabase):
        """Admin key no Authorization não funciona — isolamento entre sistemas de auth."""
        r = client.post(
            "/admin/promotions",
            json=VALID_PROMO,
            headers={"Authorization": "Bearer test-admin-key-12345"},
        )
        assert r.status_code == 422  # X-Admin-Key header obrigatório ausente

    def test_list_accessible_without_any_auth(self, client, mock_supabase):
        """Endpoint público: nenhum header necessário."""
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
        r = client.get("/promotions")
        assert r.status_code == 200
