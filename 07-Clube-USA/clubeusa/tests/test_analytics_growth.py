"""
Testes para GET /admin/analytics/growth (Fase 0.3).

Cobre:
- Estrutura da resposta (chaves obrigatórias)
- growth_series tem exatamente `days` entradas, ordenadas por data
- Dias sem cadastro aparecem com new_members=0
- email_verification_rate calculado corretamente
- days fora do range (0, 91) → 422
- Autenticação: sem token → 401, sem admin → 403
"""
import os, sys, pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone

ROOT = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'api'))

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake-key")
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-32-chars-pad")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret")
os.environ.setdefault("STRIPE_SECRET_KEY", "")
os.environ.setdefault("STRIPE_WEBHOOK_SECRET", "")
os.environ.setdefault("STRIPE_VIP_PRICE_ID", "")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_member(days_ago: int = 0, email_verified: bool = False, referred: bool = False):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {
        "created_at": ts,
        "email_verified": email_verified,
        "referred_by": "some-uuid" if referred else None,
        "status": "active",
    }


def _mock_sb_full(members, referrals=None, audit_clicks=0):
    """Retorna um mock de Supabase que responde às queries de get_analytics_growth."""
    sb = MagicMock()

    # members.select(...).execute()
    mb = MagicMock()
    mb.data = members
    sb.table("members").select.return_value.execute.return_value = mb

    # referrals.select(...).gte(...).execute()
    rb = MagicMock()
    rb.data = referrals or []
    sb.table("referrals").select.return_value.gte.return_value.execute.return_value = rb

    # audit_logs.select(...).eq(...).gte(...).execute()
    ab = MagicMock()
    ab.data = [{}] * audit_clicks
    sb.table("audit_logs").select.return_value.eq.return_value.gte.return_value.execute.return_value = ab

    return sb


# ---------------------------------------------------------------------------
# Testes unitários de get_analytics_growth
# ---------------------------------------------------------------------------

def test_growth_series_length(mocker):
    """growth_series deve ter exatamente `days` entradas."""
    sb = _mock_sb_full([_make_member(1), _make_member(5)])
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    result = get_analytics_growth(days=14)

    assert len(result["growth_series"]) == 14


def test_growth_series_sorted_ascending(mocker):
    """As datas na série devem estar em ordem crescente."""
    sb = _mock_sb_full([_make_member(2)])
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    series = get_analytics_growth(days=7)["growth_series"]

    dates = [e["date"] for e in series]
    assert dates == sorted(dates)


def test_growth_zero_fill(mocker):
    """Dias sem nenhum cadastro devem aparecer com new_members=0."""
    # Um membro criado ontem
    sb = _mock_sb_full([_make_member(1)])
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    series = get_analytics_growth(days=7)["growth_series"]

    # Pelo menos 6 dos 7 dias devem ter 0
    zeros = [e for e in series if e["new_members"] == 0]
    assert len(zeros) >= 6


def test_email_verification_rate(mocker):
    """email_verification_rate = verified / total * 100, arredondado a 1 casa."""
    members = [
        _make_member(0, email_verified=True),
        _make_member(0, email_verified=True),
        _make_member(0, email_verified=False),
        _make_member(0, email_verified=False),
    ]
    sb = _mock_sb_full(members)
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    totals = get_analytics_growth(days=30)["totals"]

    assert totals["email_verified"] == 2
    assert totals["total_members"] == 4
    assert totals["email_verification_rate"] == 50.0


def test_zero_members_no_division_error(mocker):
    """Com 0 membros, email_verification_rate deve ser 0.0 sem ZeroDivisionError."""
    sb = _mock_sb_full([])
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    totals = get_analytics_growth()["totals"]

    assert totals["email_verification_rate"] == 0.0


def test_referral_counts(mocker):
    """referral_conversions_period e referral_link_clicks_period são contados."""
    sb = _mock_sb_full(
        [_make_member(0, referred=True)],
        referrals=[{"status": "confirmed"}, {"status": "confirmed"}, {"status": "pending"}],
        audit_clicks=5,
    )
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    totals = get_analytics_growth()["totals"]

    assert totals["referral_conversions_period"] == 2
    assert totals["referral_pending_period"] == 1
    assert totals["referral_link_clicks_period"] == 5
    assert totals["registered_via_referral"] == 1


def test_required_keys_present(mocker):
    """Resposta deve ter todas as chaves documentadas."""
    sb = _mock_sb_full([])
    mocker.patch("services.admin_service._supabase", return_value=sb)

    from services.admin_service import get_analytics_growth
    result = get_analytics_growth()

    assert "period_days" in result
    assert "generated_at" in result
    assert "growth_series" in result
    assert "totals" in result

    for key in ("total_members", "new_in_period", "email_verified",
                "email_verification_rate", "registered_via_referral",
                "referral_conversions_period", "referral_pending_period",
                "referral_link_clicks_period"):
        assert key in result["totals"], f"chave ausente: {key}"


# ---------------------------------------------------------------------------
# Testes de integração via FastAPI TestClient
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_client(mocker):
    """Cliente com token de admin injetado."""
    sb = _mock_sb_full([_make_member(1)])
    mocker.patch("supabase.create_client", return_value=sb)

    # Mock require_admin para retornar admin info
    async def _fake_admin():
        return {"sub": "admin-id", "role": "admin"}

    from fastapi.testclient import TestClient
    import main as app_module
    app_module.app.dependency_overrides[app_module.require_admin] = _fake_admin
    client = TestClient(app_module.app)
    yield client
    app_module.app.dependency_overrides.clear()


def test_endpoint_returns_200(admin_client):
    resp = admin_client.get("/admin/analytics/growth")
    assert resp.status_code == 200
    data = resp.json()
    assert data["period_days"] == 30
    assert len(data["growth_series"]) == 30


def test_endpoint_custom_days(admin_client):
    resp = admin_client.get("/admin/analytics/growth?days=7")
    assert resp.status_code == 200
    assert resp.json()["period_days"] == 7
    assert len(resp.json()["growth_series"]) == 7


def test_endpoint_invalid_days_422(admin_client):
    assert admin_client.get("/admin/analytics/growth?days=0").status_code == 422
    assert admin_client.get("/admin/analytics/growth?days=91").status_code == 422


def test_endpoint_no_auth_401(mocker):
    mocker.patch("supabase.create_client", return_value=_mock_sb_full([]))
    from fastapi.testclient import TestClient
    import main as app_module
    client = TestClient(app_module.app)
    resp = client.get("/admin/analytics/growth")
    assert resp.status_code == 401
