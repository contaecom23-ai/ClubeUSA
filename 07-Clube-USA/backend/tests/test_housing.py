import pytest

VALID_HOUSING = {
    "title": "Quarto disponível — Miami, FL",
    "description": "Quarto mobiliado em casa compartilhada com 3 moradores brasileiros.",
    "listing_type": "quarto_disponivel",
}

FULL_HOUSING = {
    **VALID_HOUSING,
    "zip_code": "33101",
    "city": "Miami",
    "state": "FL",
    "rent_monthly_cents": 120000,
    "bedrooms": 1,
    "bathrooms": 2.0,
    "furnished": True,
    "utilities_included": True,
    "pets_allowed": False,
    "available_from": "2026-08-01T00:00:00Z",
    "contact_email": "test@exemplo.com",
    "contact_phone": "3051234567",
    "expires_at": "2027-12-31T23:59:59Z",
}

HOUSING_ROW = {
    "id": "housing-uuid-123",
    "title": "Quarto disponível — Miami, FL",
    "description": "Quarto mobiliado em casa compartilhada com 3 moradores brasileiros.",
    "listing_type": "quarto_disponivel",
    "zip_code": None,
    "city": None,
    "state": None,
    "rent_monthly_cents": None,
    "bedrooms": None,
    "bathrooms": None,
    "furnished": False,
    "utilities_included": False,
    "pets_allowed": None,
    "available_from": None,
    "contact_email": None,
    "contact_phone": None,
    "image_url": None,
    "expires_at": None,
    "created_at": "2026-07-12T12:00:00Z",
}

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key-12345"}


@pytest.fixture(autouse=True)
def patch_admin_key(monkeypatch):
    monkeypatch.setattr("config.settings.ADMIN_API_KEY", "test-admin-key-12345")


# ---------------------------------------------------------------------------
# Listagem pública
# ---------------------------------------------------------------------------

class TestListHousing:
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
        r = client.get("/housing")
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["has_more"] is False

    def test_list_with_items(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [HOUSING_ROW], 1)
        r = client.get("/housing")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["title"] == "Quarto disponível — Miami, FL"
        assert body["total"] == 1
        assert body["has_more"] is False

    def test_list_pagination_has_more(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [HOUSING_ROW] * 20, 50)
        r = client.get("/housing?page=1&page_size=20")
        assert r.status_code == 200
        assert r.json()["has_more"] is True

    def test_list_no_auth_required(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [], 0)
        r = client.get("/housing")
        assert r.status_code == 200

    def test_list_page_size_above_max_rejected(self, client, mock_supabase):
        r = client.get("/housing?page_size=200")
        assert r.status_code == 422

    def test_list_page_zero_rejected(self, client, mock_supabase):
        r = client.get("/housing?page=0")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET por ID
# ---------------------------------------------------------------------------

class TestGetHousing:
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
        self._setup_get_mock(mock_supabase, HOUSING_ROW)
        r = client.get("/housing/housing-uuid-123")
        assert r.status_code == 200
        assert r.json()["id"] == "housing-uuid-123"

    def test_get_not_found(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, None)
        r = client.get("/housing/nao-existe")
        assert r.status_code == 404

    def test_get_no_auth_required(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, HOUSING_ROW)
        r = client.get("/housing/housing-uuid-123")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Admin: criar anúncio
# ---------------------------------------------------------------------------

class TestCreateHousing:
    def _setup_insert_mock(self, mock_supabase, row):
        chain = (
            mock_supabase.table.return_value
            .insert.return_value
        )
        chain.execute.return_value.data = [row]

    def test_create_minimal(self, client, mock_supabase):
        self._setup_insert_mock(mock_supabase, HOUSING_ROW)
        r = client.post("/admin/housing", json=VALID_HOUSING, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        assert r.json()["title"] == "Quarto disponível — Miami, FL"

    def test_create_full(self, client, mock_supabase):
        row = {**HOUSING_ROW, **{
            "zip_code": "33101", "city": "Miami", "state": "FL",
            "rent_monthly_cents": 120000, "bedrooms": 1, "bathrooms": 2.0,
            "furnished": True, "utilities_included": True, "pets_allowed": False,
        }}
        self._setup_insert_mock(mock_supabase, row)
        r = client.post("/admin/housing", json=FULL_HOUSING, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        body = r.json()
        assert body["rent_monthly_cents"] == 120000
        assert body["furnished"] is True

    def test_create_no_admin_key_rejected(self, client, mock_supabase):
        r = client.post("/admin/housing", json=VALID_HOUSING)
        assert r.status_code == 422

    def test_create_wrong_admin_key_rejected(self, client, mock_supabase):
        r = client.post("/admin/housing", json=VALID_HOUSING, headers={"X-Admin-Key": "wrong"})
        assert r.status_code == 401

    def test_create_empty_title_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "title": ""}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_title_too_long_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "title": "x" * 121}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_invalid_listing_type_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "listing_type": "tipo_invalido"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_invalid_zip_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "zip_code": "123"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_invalid_state_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "state": "XX"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_negative_rent_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "rent_monthly_cents": -1}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_invalid_url_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "image_url": "nao-e-url"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_create_all_listing_types_accepted(self, client, mock_supabase):
        for lt in ["quarto_disponivel", "precisa_quarto", "casa_disponivel"]:
            self._setup_insert_mock(mock_supabase, {**HOUSING_ROW, "listing_type": lt})
            r = client.post("/admin/housing", json={**VALID_HOUSING, "listing_type": lt}, headers=ADMIN_HEADERS)
            assert r.status_code == 201, f"listing_type {lt!r} rejeitado inesperadamente"


# ---------------------------------------------------------------------------
# Admin: desativar anúncio
# ---------------------------------------------------------------------------

class TestDeactivateHousing:
    def _setup_update_mock(self, mock_supabase, data):
        chain = (
            mock_supabase.table.return_value
            .update.return_value
            .eq.return_value
        )
        chain.execute.return_value.data = data

    def test_deactivate_existing(self, client, mock_supabase):
        self._setup_update_mock(mock_supabase, [HOUSING_ROW])
        r = client.delete("/admin/housing/housing-uuid-123", headers=ADMIN_HEADERS)
        assert r.status_code == 204

    def test_deactivate_not_found(self, client, mock_supabase):
        self._setup_update_mock(mock_supabase, [])
        r = client.delete("/admin/housing/nao-existe", headers=ADMIN_HEADERS)
        assert r.status_code == 404

    def test_deactivate_no_admin_key_rejected(self, client, mock_supabase):
        r = client.delete("/admin/housing/housing-uuid-123")
        assert r.status_code == 422

    def test_deactivate_wrong_key_rejected(self, client, mock_supabase):
        r = client.delete("/admin/housing/housing-uuid-123", headers={"X-Admin-Key": "wrong"})
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# Busca por ZIP + raio
# ---------------------------------------------------------------------------

class TestZipSearch:
    def _setup_zip_coords_mock(self, mock_supabase, coords_data):
        zip_chain = (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .maybe_single.return_value
        )
        zip_chain.execute.return_value.data = coords_data

    def _setup_search_list_mock(self, mock_supabase, data):
        list_chain = (
            mock_supabase.table.return_value
            .select.return_value
            .eq.return_value
            .or_.return_value
        )
        list_chain.execute.return_value.data = data

    def test_search_invalid_zip_format(self, client, mock_supabase):
        r = client.get("/housing/search?zip=123")
        assert r.status_code == 422

    def test_search_zip_not_in_db(self, client, mock_supabase):
        self._setup_zip_coords_mock(mock_supabase, None)
        r = client.get("/housing/search?zip=99999")
        assert r.status_code == 422

    def test_search_response_has_required_fields(self, client, mock_supabase):
        self._setup_zip_coords_mock(mock_supabase, {"latitude": 25.77, "longitude": -80.19})
        self._setup_search_list_mock(mock_supabase, [])
        r = client.get("/housing/search?zip=33101")
        assert r.status_code == 200
        body = r.json()
        assert body["search_zip"] == "33101"
        assert body["radius_miles"] == 10.0
        assert body["items"] == []

    def test_search_radius_above_max_rejected(self, client, mock_supabase):
        r = client.get("/housing/search?zip=33101&radius=100")
        assert r.status_code == 422

    def test_search_filters_by_distance(self, client, mock_supabase):
        """Anúncio com ZIP fora do raio deve ser filtrado."""
        self._setup_zip_coords_mock(mock_supabase, {"latitude": 25.77, "longitude": -80.19})
        far_row = {
            **HOUSING_ROW,
            "latitude": 40.71,
            "longitude": -74.00,
        }
        self._setup_search_list_mock(mock_supabase, [far_row])
        r = client.get("/housing/search?zip=33101&radius=10")
        assert r.status_code == 200
        assert r.json()["total"] == 0

    def test_search_includes_listings_without_zip(self, client, mock_supabase):
        """Anúncio sem lat/lng (sem ZIP) sempre aparece no resultado."""
        self._setup_zip_coords_mock(mock_supabase, {"latitude": 25.77, "longitude": -80.19})
        no_zip_row = {**HOUSING_ROW, "latitude": None, "longitude": None}
        self._setup_search_list_mock(mock_supabase, [no_zip_row])
        r = client.get("/housing/search?zip=33101&radius=5")
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 1
        assert body["items"][0]["distance_miles"] is None

    def test_search_via_main_endpoint_with_zip(self, client, mock_supabase):
        """GET /housing?zip=XXXXX deve retornar 200 (mesma shape de HousingListResponse).
        A resposta enriquecida com search_zip vem de GET /housing/search."""
        self._setup_zip_coords_mock(mock_supabase, {"latitude": 25.77, "longitude": -80.19})
        self._setup_search_list_mock(mock_supabase, [])
        r = client.get("/housing?zip=33101&radius=15")
        assert r.status_code == 200
        body = r.json()
        assert "items" in body
        assert "total" in body


# ---------------------------------------------------------------------------
# Validação de campos específicos
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    def test_valid_states_accepted(self, client, mock_supabase):
        chain = mock_supabase.table.return_value.insert.return_value
        chain.execute.return_value.data = [HOUSING_ROW]
        for state in ["FL", "NY", "CA", "TX", "MA", "NJ", "IL", "DC"]:
            payload = {**VALID_HOUSING, "state": state}
            r = client.post("/admin/housing", json=payload, headers=ADMIN_HEADERS)
            assert r.status_code == 201, f"Estado {state!r} rejeitado inesperadamente"

    def test_invalid_state_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "state": "ZZ"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_bedrooms_out_of_range_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "bedrooms": 25}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_contact_phone_too_short_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "contact_phone": "123"}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422

    def test_contact_phone_valid(self, client, mock_supabase):
        chain = mock_supabase.table.return_value.insert.return_value
        chain.execute.return_value.data = [HOUSING_ROW]
        good = {**VALID_HOUSING, "contact_phone": "3051234567"}
        r = client.post("/admin/housing", json=good, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_description_too_long_rejected(self, client, mock_supabase):
        bad = {**VALID_HOUSING, "description": "x" * 2001}
        r = client.post("/admin/housing", json=bad, headers=ADMIN_HEADERS)
        assert r.status_code == 422
