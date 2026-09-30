# tests/test_jobs.py — Fase 1.4: Empregos
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import FastAPI

# ── Helpers ────────────────────────────────────────────────────

def _make_job(**kwargs):
    defaults = {
        "id": "job-uuid-1",
        "title": "Pedreiro",
        "company": "Construtora ABC",
        "description": "Experiência em alvenaria.",
        "city": "Miami",
        "state_code": "FL",
        "zip_code": "33101",
        "employment_type": "full_time",
        "category": "construction",
        "salary_min": 18.0,
        "salary_max": 25.0,
        "salary_period": "hour",
        "contact_url": "https://example.com/apply",
        "language": "pt",
        "is_active": True,
        "expires_at": None,
        "posted_by_admin": True,
        "created_at": "2026-09-30T10:00:00Z",
        "updated_at": "2026-09-30T10:00:00Z",
    }
    defaults.update(kwargs)
    return defaults


# ── Unit: _is_expired ──────────────────────────────────────────

def test_is_expired_none():
    from routers.jobs import _is_expired
    assert _is_expired({"expires_at": None}) is False


def test_is_expired_past():
    from routers.jobs import _is_expired
    assert _is_expired({"expires_at": "2020-01-01T00:00:00Z"}) is True


def test_is_expired_future():
    from routers.jobs import _is_expired
    assert _is_expired({"expires_at": "2099-01-01T00:00:00Z"}) is False


# ── Unit: JobCreate validation ─────────────────────────────────

def test_job_create_invalid_employment_type():
    from pydantic import ValidationError
    from routers.jobs import JobCreate
    with pytest.raises(ValidationError, match="employment_type"):
        JobCreate(title="T", company="C", description="D", employment_type="full_week")


def test_job_create_invalid_category():
    from pydantic import ValidationError
    from routers.jobs import JobCreate
    with pytest.raises(ValidationError, match="category"):
        JobCreate(title="T", company="C", description="D", category="magic")


def test_job_create_salary_range_reversed():
    from pydantic import ValidationError
    from routers.jobs import JobCreate
    with pytest.raises(ValidationError, match="salary_min"):
        JobCreate(title="T", company="C", description="D", salary_min=50.0, salary_max=10.0)


def test_job_create_empty_title_rejected():
    from pydantic import ValidationError
    from routers.jobs import JobCreate
    with pytest.raises(ValidationError):
        JobCreate(title="   ", company="C", description="D")


def test_job_create_invalid_zip():
    from pydantic import ValidationError
    from routers.jobs import JobCreate
    with pytest.raises(ValidationError, match="zip_code"):
        JobCreate(title="T", company="C", description="D", zip_code="ABCDE")


def test_job_create_valid():
    from routers.jobs import JobCreate
    job = JobCreate(
        title="Cozinheiro",
        company="Restaurante XYZ",
        description="Preparo de pratos brasileiros.",
        category="food_service",
        employment_type="part_time",
        salary_min=15.0,
        salary_max=20.0,
        salary_period="hour",
        zip_code="33101",
        state_code="FL",
        language="pt",
    )
    assert job.title == "Cozinheiro"
    assert job.category == "food_service"


# ── Integration: FastAPI TestClient ────────────────────────────

@pytest.fixture
def app_client(mocker):
    """Mount only the jobs router in a minimal FastAPI app with mocked Supabase."""
    from routers.jobs import router
    app = FastAPI()
    app.include_router(router)

    mock_sb = MagicMock()
    mocker.patch("routers.jobs._sb", return_value=mock_sb)

    with TestClient(app, raise_server_exceptions=True) as c:
        yield c, mock_sb


def test_list_categories(app_client):
    client, _ = app_client
    resp = client.get("/jobs/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert "categories" in data
    assert "construction" in data["categories"]
    assert "employment_types" in data
    assert "salary_periods" in data


def test_list_jobs_empty(app_client):
    client, mock_sb = app_client
    mock_sb.table().select().eq().order().limit().offset().execute.return_value.data = []
    resp = client.get("/jobs")
    assert resp.status_code == 200
    assert resp.json()["jobs"] == []


def test_list_jobs_returns_active(app_client):
    client, mock_sb = app_client
    job = _make_job()
    mock_sb.table().select().eq().order().limit().offset().execute.return_value.data = [job]
    resp = client.get("/jobs")
    assert resp.status_code == 200
    jobs = resp.json()["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Pedreiro"


def test_list_jobs_expired_filtered(app_client):
    client, mock_sb = app_client
    job = _make_job(expires_at="2020-01-01T00:00:00Z")  # past date
    mock_sb.table().select().eq().order().limit().offset().execute.return_value.data = [job]
    resp = client.get("/jobs")
    assert resp.status_code == 200
    assert resp.json()["jobs"] == []


def test_list_jobs_invalid_category_rejected(app_client):
    client, _ = app_client
    resp = client.get("/jobs?category=invalid_category")
    assert resp.status_code == 400


def test_list_jobs_limit_capped_at_50(app_client):
    """Limit param > 50 should be rejected by FastAPI Query(ge=1, le=50)."""
    client, mock_sb = app_client
    mock_sb.table().select().eq().order().limit().offset().execute.return_value.data = []
    resp = client.get("/jobs?limit=200")
    assert resp.status_code == 422  # validation error


def test_get_job_found(app_client):
    client, mock_sb = app_client
    job = _make_job()
    mock_sb.table().select().eq().eq().execute.return_value.data = [job]
    resp = client.get("/jobs/job-uuid-1")
    assert resp.status_code == 200
    assert resp.json()["id"] == "job-uuid-1"


def test_get_job_not_found(app_client):
    client, mock_sb = app_client
    mock_sb.table().select().eq().eq().execute.return_value.data = []
    resp = client.get("/jobs/nonexistent-id")
    assert resp.status_code == 404


def test_get_job_expired_returns_404(app_client):
    client, mock_sb = app_client
    job = _make_job(expires_at="2020-01-01T00:00:00Z")
    mock_sb.table().select().eq().eq().execute.return_value.data = [job]
    resp = client.get("/jobs/job-uuid-1")
    assert resp.status_code == 404


# ── Admin: require_admin gate ─────────────────────────────────

def test_admin_create_job_no_auth_rejected(app_client):
    client, _ = app_client
    resp = client.post("/jobs/admin/jobs", json={
        "title": "Test", "company": "Co", "description": "Desc"
    })
    assert resp.status_code == 401


def test_admin_create_job_wrong_token_rejected(app_client, monkeypatch):
    client, _ = app_client
    monkeypatch.setenv("ADMIN_SECRET", "correct-secret")
    resp = client.post(
        "/jobs/admin/jobs",
        json={"title": "Test", "company": "Co", "description": "Desc"},
        headers={"Authorization": "Bearer wrong-secret"},
    )
    assert resp.status_code == 401


def test_admin_create_job_success(app_client, monkeypatch):
    client, mock_sb = app_client
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
    job = _make_job()
    mock_sb.table().insert().execute.return_value.data = [job]
    resp = client.post(
        "/jobs/admin/jobs",
        json={
            "title": "Pedreiro",
            "company": "Construtora ABC",
            "description": "Experiência em alvenaria.",
            "category": "construction",
            "employment_type": "full_time",
        },
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 201
    assert resp.json()["title"] == "Pedreiro"


def test_admin_update_job_not_found(app_client, monkeypatch):
    client, mock_sb = app_client
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
    mock_sb.table().select().eq().execute.return_value.data = []
    resp = client.put(
        "/jobs/admin/jobs/nonexistent",
        json={"title": "New Title"},
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 404


def test_admin_deactivate_job_success(app_client, monkeypatch):
    client, mock_sb = app_client
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
    mock_sb.table().select().eq().execute.return_value.data = [{"id": "job-1", "is_active": True}]
    mock_sb.table().update().eq().execute.return_value.data = [{"id": "job-1", "is_active": False}]
    resp = client.delete(
        "/jobs/admin/jobs/job-1",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_admin_deactivate_job_not_found(app_client, monkeypatch):
    client, mock_sb = app_client
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
    mock_sb.table().select().eq().execute.return_value.data = []
    resp = client.delete(
        "/jobs/admin/jobs/nonexistent",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 404


def test_admin_list_jobs(app_client, monkeypatch):
    client, mock_sb = app_client
    monkeypatch.setenv("ADMIN_SECRET", "test-secret")
    jobs = [_make_job(), _make_job(id="job-uuid-2", is_active=False)]
    mock_sb.table().select().order().limit().offset().execute.return_value.data = jobs
    resp = client.get(
        "/jobs/admin/jobs",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert resp.status_code == 200
    assert len(resp.json()["jobs"]) == 2


def test_admin_list_jobs_no_auth(app_client):
    client, _ = app_client
    resp = client.get("/jobs/admin/jobs")
    assert resp.status_code == 401
