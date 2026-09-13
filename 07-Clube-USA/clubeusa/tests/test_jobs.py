# tests/test_jobs.py — Clube USA — Fase 1.4
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.fixture
def mock_sb():
    with patch("services.job_service._supabase") as mock:
        sb = MagicMock()
        mock.return_value = sb
        yield sb


def _make_job(**kwargs):
    base = {
        "id": "job-uuid-001",
        "title": "Limpeza Comercial",
        "company": "Clean Pro LLC",
        "description": "Vaga de limpeza em escritórios — turno manhã",
        "location_city": "Orlando",
        "location_state": "FL",
        "zip_code": "32801",
        "job_type": "full_time",
        "salary_min": 14,
        "salary_max": 18,
        "salary_period": "hour",
        "contact_email": "jobs@cleanpro.com",
        "contact_url": None,
        "posted_by": None,
        "is_active": True,
        "expires_at": None,
        "created_at": "2026-09-13T10:00:00Z",
        "updated_at": "2026-09-13T10:00:00Z",
    }
    base.update(kwargs)
    return base


def _chain_list(mock_sb, data):
    """Monta a cadeia de chamadas para list_jobs."""
    q = MagicMock()
    q.execute.return_value.data = data
    chain = mock_sb.table.return_value.select.return_value.eq.return_value
    chain.order.return_value.limit.return_value.offset.return_value.or_.return_value = q
    return q


# ── list_jobs ────────────────────────────────────────────────

class TestListJobs:
    def test_returns_empty_when_no_jobs(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.job_service import list_jobs
        assert list_jobs() == []

    def test_returns_active_jobs(self, mock_sb):
        _chain_list(mock_sb, [_make_job()])
        from services.job_service import list_jobs
        result = list_jobs()
        assert len(result) == 1
        assert result[0]["title"] == "Limpeza Comercial"

    def test_limit_capped_at_100(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.job_service import list_jobs
        list_jobs(limit=9999)
        limit_call = mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit
        assert limit_call.call_args[0][0] == 100

    def test_ignores_unknown_job_type_filter(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.job_service import list_jobs
        # invalid job_type must not add eq filter — just return empty
        result = list_jobs(job_type="flying_cars")
        assert result == []


# ── get_job ──────────────────────────────────────────────────

class TestGetJob:
    def _chain_get(self, mock_sb, data):
        q = MagicMock()
        q.execute.return_value.data = data
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value = q

    def test_returns_none_when_not_found(self, mock_sb):
        self._chain_get(mock_sb, [])
        from services.job_service import get_job
        assert get_job("nonexistent") is None

    def test_returns_job(self, mock_sb):
        self._chain_get(mock_sb, [_make_job()])
        from services.job_service import get_job
        result = get_job("job-uuid-001")
        assert result is not None
        assert result["id"] == "job-uuid-001"

    def test_expired_job_returns_none(self, mock_sb):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self._chain_get(mock_sb, [_make_job(expires_at=past)])
        from services.job_service import get_job
        assert get_job("job-uuid-001") is None

    def test_non_expired_job_returned(self, mock_sb):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        self._chain_get(mock_sb, [_make_job(expires_at=future)])
        from services.job_service import get_job
        result = get_job("job-uuid-001")
        assert result is not None


# ── create_job ───────────────────────────────────────────────

class TestCreateJob:
    def _mock_insert(self, mock_sb, data):
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = data

    def test_creates_job_successfully(self, mock_sb):
        self._mock_insert(mock_sb, [_make_job()])
        from services.job_service import create_job
        result = create_job(
            title="Limpeza Comercial",
            company="Clean Pro LLC",
            description="Vaga de limpeza em escritórios — turno manhã",
        )
        assert result["id"] == "job-uuid-001"
        mock_sb.table.return_value.insert.assert_called_once()

    def test_rejects_invalid_job_type(self, mock_sb):
        from services.job_service import create_job
        with pytest.raises(ValueError, match="job_type"):
            create_job(
                title="Vaga X",
                company="Empresa",
                description="Descrição longa o suficiente para criar vaga",
                job_type="flying_car",
            )

    def test_rejects_invalid_salary_period(self, mock_sb):
        from services.job_service import create_job
        with pytest.raises(ValueError, match="salary_period"):
            create_job(
                title="Vaga X",
                company="Empresa",
                description="Descrição longa o suficiente para criar vaga",
                salary_period="second",
            )

    def test_rejects_salary_min_greater_than_max(self, mock_sb):
        from services.job_service import create_job
        with pytest.raises(ValueError, match="salary_min"):
            create_job(
                title="Vaga X",
                company="Empresa",
                description="Descrição longa o suficiente para criar vaga",
                salary_min=100,
                salary_max=50,
            )

    def test_raises_on_db_failure(self, mock_sb):
        self._mock_insert(mock_sb, [])
        from services.job_service import create_job
        with pytest.raises(RuntimeError, match="Falha"):
            create_job(
                title="Vaga X",
                company="Empresa",
                description="Descrição longa o suficiente para criar vaga",
            )

    def test_truncates_long_title(self, mock_sb):
        self._mock_insert(mock_sb, [_make_job()])
        from services.job_service import create_job
        create_job(
            title="A" * 300,
            company="Empresa",
            description="Descrição longa o suficiente para criar vaga",
        )
        inserted = mock_sb.table.return_value.insert.call_args[0][0]
        assert len(inserted["title"]) == 200


# ── deactivate_job ───────────────────────────────────────────

class TestDeactivateJob:
    def test_deactivates_job(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [_make_job(is_active=False)]
        from services.job_service import deactivate_job
        assert deactivate_job("job-uuid-001") is True

    def test_returns_false_for_missing_job(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
        from services.job_service import deactivate_job
        assert deactivate_job("nonexistent") is False


# ── isolation: member_id never from client ───────────────────

class TestIsolation:
    def test_list_jobs_does_not_expose_posted_by(self, mock_sb):
        """
        list_jobs retorna apenas campos públicos — contact_email e posted_by
        não são incluídos no select de listagem para evitar vazamento de PII.
        """
        _chain_list(mock_sb, [])
        from services.job_service import list_jobs
        list_jobs()
        select_call = mock_sb.table.return_value.select.call_args[0][0]
        # posted_by não deve aparecer no select de listagem
        assert "posted_by" not in select_call
        assert "contact_email" not in select_call
