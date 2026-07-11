import pytest

from tests.conftest import make_jwt

VALID_JOB = {
    "title": "Auxiliar de Cozinha",
    "company": "Restaurante Sabor Brasil",
    "description": "Procuramos auxiliar de cozinha com experiência. Horário: 10h às 18h.",
    "category": "restaurante",
    "job_type": "full_time",
}

FULL_JOB = {
    **VALID_JOB,
    "zip_code": "33101",
    "salary_range": "$15-17/hr",
    "apply_url": "https://example.com/apply",
    "contact_email": "jobs@saborbrasil.com",
    "expires_at": "2027-12-31T23:59:59Z",
}

JOB_ROW = {
    "id": "job-uuid-123",
    "title": "Auxiliar de Cozinha",
    "company": "Restaurante Sabor Brasil",
    "description": "Procuramos auxiliar de cozinha com experiência. Horário: 10h às 18h.",
    "category": "restaurante",
    "job_type": "full_time",
    "zip_code": None,
    "salary_range": None,
    "apply_url": None,
    "contact_email": None,
    "expires_at": None,
    "created_at": "2026-07-11T12:00:00Z",
}

ADMIN_HEADERS = {"X-Admin-Key": "test-admin-key-12345"}


@pytest.fixture(autouse=True)
def patch_admin_key(monkeypatch):
    monkeypatch.setattr("config.settings.ADMIN_API_KEY", "test-admin-key-12345")


# ---------------------------------------------------------------------------
# Listagem pública
# ---------------------------------------------------------------------------


class TestListJobs:
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
        r = client.get("/jobs")
        assert r.status_code == 200
        body = r.json()
        assert body["items"] == []
        assert body["total"] == 0
        assert body["has_more"] is False

    def test_list_with_items(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [JOB_ROW], 1)
        r = client.get("/jobs")
        assert r.status_code == 200
        body = r.json()
        assert len(body["items"]) == 1
        assert body["items"][0]["title"] == "Auxiliar de Cozinha"
        assert body["items"][0]["company"] == "Restaurante Sabor Brasil"
        assert body["total"] == 1
        assert body["has_more"] is False

    def test_list_pagination(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [JOB_ROW] * 20, 50)
        r = client.get("/jobs?page=1&page_size=20")
        assert r.status_code == 200
        body = r.json()
        assert body["has_more"] is True
        assert body["total"] == 50

    def test_list_no_auth_required(self, client, mock_supabase):
        self._setup_list_mock(mock_supabase, [], 0)
        r = client.get("/jobs")  # sem Authorization
        assert r.status_code == 200

    def test_list_page_size_above_max_rejected(self, client, mock_supabase):
        r = client.get("/jobs?page_size=200")
        assert r.status_code == 422

    def test_list_page_zero_rejected(self, client, mock_supabase):
        r = client.get("/jobs?page=0")
        assert r.status_code == 422

    def test_list_invalid_zip_rejected(self, client, mock_supabase):
        r = client.get("/jobs?zip=ABCDE")
        assert r.status_code == 422

    def test_list_zip_too_short_rejected(self, client, mock_supabase):
        r = client.get("/jobs?zip=1234")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Get por ID (público)
# ---------------------------------------------------------------------------


class TestGetJob:
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
        self._setup_get_mock(mock_supabase, JOB_ROW)
        r = client.get("/jobs/job-uuid-123")
        assert r.status_code == 200
        assert r.json()["id"] == "job-uuid-123"
        assert r.json()["category"] == "restaurante"

    def test_get_not_found(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, None)
        r = client.get("/jobs/nonexistent-id")
        assert r.status_code == 404

    def test_get_no_auth_required(self, client, mock_supabase):
        self._setup_get_mock(mock_supabase, JOB_ROW)
        r = client.get("/jobs/job-uuid-123")
        assert r.status_code == 200


# ---------------------------------------------------------------------------
# Criação (admin)
# ---------------------------------------------------------------------------


class TestCreateJob:
    def _setup_insert_mock(self, mock_supabase, row):
        mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [row]

    def test_create_minimal_fields(self, client, mock_supabase):
        self._setup_insert_mock(mock_supabase, {**JOB_ROW, "id": "new-uuid"})
        r = client.post("/admin/jobs", json=VALID_JOB, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        assert r.json()["company"] == "Restaurante Sabor Brasil"
        assert r.json()["category"] == "restaurante"
        assert r.json()["job_type"] == "full_time"

    def test_create_all_fields(self, client, mock_supabase):
        full_row = {
            **JOB_ROW,
            "id": "new-uuid-full",
            "zip_code": "33101",
            "salary_range": "$15-17/hr",
            "apply_url": "https://example.com/apply",
            "contact_email": "jobs@saborbrasil.com",
        }
        self._setup_insert_mock(mock_supabase, full_row)
        r = client.post("/admin/jobs", json=FULL_JOB, headers=ADMIN_HEADERS)
        assert r.status_code == 201

    def test_create_wrong_admin_key(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json=VALID_JOB,
            headers={"X-Admin-Key": "wrong-key"},
        )
        assert r.status_code == 401

    def test_create_missing_admin_key(self, client, mock_supabase):
        r = client.post("/admin/jobs", json=VALID_JOB)
        assert r.status_code == 422

    def test_create_empty_title_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "title": "   "},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_title_too_long_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "title": "x" * 121},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_category(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "category": "invalid_cat"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_job_type(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "job_type": "invalid_type"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_zip_letters(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "zip_code": "ABCDE"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_zip_too_short(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "zip_code": "1234"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_apply_url(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "apply_url": "not-a-url"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_invalid_email(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "contact_email": "not-an-email"},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_salary_range_too_long_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "salary_range": "x" * 101},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_description_too_long_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json={**VALID_JOB, "description": "x" * 2001},
            headers=ADMIN_HEADERS,
        )
        assert r.status_code == 422

    def test_create_missing_required_fields(self, client, mock_supabase):
        for field in ("title", "company", "description", "category", "job_type"):
            payload = {k: v for k, v in VALID_JOB.items() if k != field}
            r = client.post("/admin/jobs", json=payload, headers=ADMIN_HEADERS)
            assert r.status_code == 422, f"Campo {field!r} ausente deveria retornar 422"

    def test_create_all_valid_job_types(self, client, mock_supabase):
        for jtype in ("full_time", "part_time", "contract", "gig"):
            row = {**JOB_ROW, "id": f"uuid-{jtype}", "job_type": jtype}
            self._setup_insert_mock(mock_supabase, row)
            r = client.post(
                "/admin/jobs",
                json={**VALID_JOB, "job_type": jtype},
                headers=ADMIN_HEADERS,
            )
            assert r.status_code == 201, f"job_type={jtype!r} deve ser aceito"

    def test_create_all_valid_categories(self, client, mock_supabase):
        cats = [
            "construcao", "limpeza", "restaurante", "motorista", "cuidado",
            "beleza", "vendas", "escritorio", "tecnologia", "saude", "outros",
        ]
        for cat in cats:
            row = {**JOB_ROW, "id": f"uuid-{cat}", "category": cat}
            self._setup_insert_mock(mock_supabase, row)
            r = client.post(
                "/admin/jobs",
                json={**VALID_JOB, "category": cat},
                headers=ADMIN_HEADERS,
            )
            assert r.status_code == 201, f"category={cat!r} deve ser aceito"

    def test_create_admin_key_not_leaked_in_response(self, client, mock_supabase):
        self._setup_insert_mock(mock_supabase, {**JOB_ROW, "id": "uuid-leak-test"})
        r = client.post("/admin/jobs", json=VALID_JOB, headers=ADMIN_HEADERS)
        assert r.status_code == 201
        assert "test-admin-key-12345" not in r.text


# ---------------------------------------------------------------------------
# Desativação (admin)
# ---------------------------------------------------------------------------


class TestDeactivateJob:
    def _setup_deactivate_mock(self, mock_supabase, data):
        chain = (
            mock_supabase.table.return_value
            .update.return_value
            .eq.return_value
        )
        chain.execute.return_value.data = data

    def test_deactivate_success(self, client, mock_supabase):
        self._setup_deactivate_mock(mock_supabase, [{"id": "job-uuid-123", "active": False}])
        r = client.delete("/admin/jobs/job-uuid-123", headers=ADMIN_HEADERS)
        assert r.status_code == 204

    def test_deactivate_not_found(self, client, mock_supabase):
        self._setup_deactivate_mock(mock_supabase, [])
        r = client.delete("/admin/jobs/nonexistent", headers=ADMIN_HEADERS)
        assert r.status_code == 404

    def test_deactivate_wrong_key(self, client, mock_supabase):
        r = client.delete(
            "/admin/jobs/job-uuid-123",
            headers={"X-Admin-Key": "wrong"},
        )
        assert r.status_code == 401

    def test_deactivate_no_key(self, client, mock_supabase):
        r = client.delete("/admin/jobs/job-uuid-123")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Busca por ZIP (serviço: unit tests)
# ---------------------------------------------------------------------------


class TestJobSearchByZip:
    def _setup_zip_lookup(self, mock_supabase, coords):
        mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
            {"latitude": coords[0], "longitude": coords[1]} if coords else None
        )

    def test_search_zip_not_found_raises_value_error(self, mock_supabase):
        from jobs.service import search_jobs_by_zip

        self._setup_zip_lookup(mock_supabase, None)
        with pytest.raises(ValueError, match="não encontrado"):
            search_jobs_by_zip(mock_supabase, zip_code="99999", radius_miles=5.0)

    def test_search_via_endpoint_unknown_zip_returns_422(self, client, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
        r = client.get("/jobs/search?zip=99999")
        assert r.status_code == 422

    def test_search_invalid_zip_format_rejected(self, client, mock_supabase):
        r = client.get("/jobs/search?zip=ABCDE")
        assert r.status_code == 422

    def test_search_radius_too_large_rejected(self, client, mock_supabase):
        r = client.get("/jobs/search?zip=33101&radius=100")
        assert r.status_code == 422

    def test_search_radius_zero_rejected(self, client, mock_supabase):
        r = client.get("/jobs/search?zip=33101&radius=0")
        assert r.status_code == 422


# ---------------------------------------------------------------------------
# Segurança: isolamento admin/usuário
# ---------------------------------------------------------------------------


class TestJobSecurity:
    def test_user_bearer_token_cannot_create(self, client, mock_supabase):
        token = make_jwt("user-123")
        r = client.post(
            "/admin/jobs",
            json=VALID_JOB,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422  # X-Admin-Key obrigatório ausente

    def test_admin_key_as_bearer_rejected(self, client, mock_supabase):
        r = client.post(
            "/admin/jobs",
            json=VALID_JOB,
            headers={"Authorization": "Bearer test-admin-key-12345"},
        )
        assert r.status_code == 422

    def test_list_accessible_without_any_auth(self, client, mock_supabase):
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
        r = client.get("/jobs")
        assert r.status_code == 200

    def test_deactivate_requires_admin_key(self, client, mock_supabase):
        token = make_jwt("user-123")
        r = client.delete(
            "/admin/jobs/job-uuid-123",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 422
