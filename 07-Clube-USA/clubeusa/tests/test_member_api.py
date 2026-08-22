"""Testes dos endpoints de membro: profile, deals, referral, click, leaderboard."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-dummy-value-32b")
os.environ.setdefault("SECRET_KEY", "test-secret-key-dummy-value-for-jwt-32b")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("APP_URL", "https://clubeusa.com")

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest


def _client_free():
    from main import app
    import deps
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-free", "plan": "free"}
    return TestClient(app)


def _client_vip():
    from main import app
    import deps
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-vip", "plan": "vip"}
    app.dependency_overrides[deps.require_paid_plan] = lambda: {"sub": "m-vip", "plan": "vip"}
    return TestClient(app)


# --- GET /member/profile ---

def test_get_profile_returns_member_data(mocker):
    mocker.patch(
        "services.member_service.get_member_profile",
        return_value={"id": "m-free", "name": "Joao", "plan": "free"},
    )
    resp = _client_free().get("/member/profile")
    assert resp.status_code == 200
    assert resp.json()["id"] == "m-free"


def test_get_profile_uses_token_sub_not_client_input(mocker):
    """O perfil retornado deve ser do membro do token, nao de um id arbitrario."""
    mock_get = mocker.patch(
        "services.member_service.get_member_profile",
        return_value={"id": "m-free", "name": "Alice"},
    )
    _client_free().get("/member/profile")
    # Servico deve ter sido chamado com o sub do token, nao com input do cliente
    mock_get.assert_called_once_with("m-free")


def test_get_profile_not_found_returns_404(mocker):
    mocker.patch("services.member_service.get_member_profile", return_value=None)
    resp = _client_free().get("/member/profile")
    assert resp.status_code == 404


# --- PATCH /member/profile ---

def test_patch_profile_valid_categories_returns_200(mocker):
    mocker.patch(
        "services.member_service.update_member_categories",
        return_value={"id": "m-free", "categories": ["electronics"]},
    )
    resp = _client_free().patch("/member/profile", json={"categories": ["electronics"]})
    assert resp.status_code == 200


def test_patch_profile_invalid_categories_filtered_no_500(mocker):
    """Categorias invalidas sao filtradas internamente — nao deve retornar 500."""
    mocker.patch(
        "services.member_service.update_member_categories",
        return_value={"id": "m-free", "categories": ["all"]},
    )
    resp = _client_free().patch("/member/profile", json={"categories": ["invalida_xyz"]})
    assert resp.status_code == 200


def test_patch_profile_uses_token_sub(mocker):
    """PATCH de categorias deve atualizar o membro do token, nao outro."""
    mock_update = mocker.patch(
        "services.member_service.update_member_categories",
        return_value={"id": "m-free", "categories": ["all"]},
    )
    _client_free().patch("/member/profile", json={"categories": ["fitness"]})
    mock_update.assert_called_once_with("m-free", ["fitness"])


# --- GET /member/deals ---

def test_get_deals_free_member(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"id": "d1", "title": "TV 55''", "status": "sent", "score": 90, "category": "electronics"},
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().get("/member/deals")
    assert resp.status_code == 200
    data = resp.json()
    assert "deals" in data
    assert data["plan"] == "free"


def test_get_deals_vip_member(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.in_.return_value.order.return_value.limit.return_value.execute.return_value.data = [
        {"id": "d2", "title": "AirPods", "status": "approved", "score": 95, "category": "electronics"},
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_vip().get("/member/deals")
    assert resp.status_code == 200
    data = resp.json()
    assert data["plan"] == "vip"


def test_get_deals_with_category_filter(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.in_.return_value.order.return_value.limit.return_value.eq.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().get("/member/deals?category=kitchen")
    assert resp.status_code == 200


# --- GET /member/referral ---

def test_get_referral_returns_link_with_code(mocker):
    mock_sb = MagicMock()
    member_result = MagicMock()
    member_result.data = [
        {"referral_code": "ABC123", "referral_count": 5, "points": 1000, "level": "partner"}
    ]
    refs_result = MagicMock()
    refs_result.data = []
    # Primeira chamada: member data; segunda: referrals history
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = member_result
    mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = refs_result
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().get("/member/referral")
    assert resp.status_code == 200
    data = resp.json()
    assert data["referral_code"] == "ABC123"
    assert "clubeusa.com/i/ABC123" in data["referral_link"]
    assert data["referral_count"] == 5
    assert data["points_earned"] == 5 * 200


def test_get_referral_not_found_returns_404(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().get("/member/referral")
    assert resp.status_code == 404


# --- POST /member/click ---

def test_click_valid_deal_returns_tracked_url(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "d1", "affiliate_url": "https://amazon.com/dp/B001?tag=abc"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    mocker.patch("services.member_service.track_click", return_value="utm-xyz-123")
    resp = _client_free().post("/member/click", json={"deal_id": "d1"})
    assert resp.status_code == 200
    data = resp.json()
    assert "url" in data
    assert "utm_source=clubeusa" in data["url"]
    assert "utm_medium=whatsapp" in data["url"]


def test_click_invalid_deal_returns_404(mocker):
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().post("/member/click", json={"deal_id": "deal-inexistente"})
    assert resp.status_code == 404


def test_click_uses_token_sub_for_tracking(mocker):
    """O rastreio de cliques deve usar o sub do token, nao input do cliente."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "d1", "affiliate_url": "https://amazon.com/dp/B001?tag=abc"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    mock_track = mocker.patch("services.member_service.track_click", return_value="utm-ok")
    _client_free().post("/member/click", json={"deal_id": "d1"})
    assert mock_track.call_args[1]["member_id"] == "m-free"


# --- GET /member/leaderboard ---

def test_leaderboard_returns_list_and_rank(mocker):
    mock_sb = MagicMock()
    mock_sb.rpc.return_value.execute.return_value.data = [
        {"position": 1, "name_display": "Jo***", "points": 5000},
        {"position": 2, "name_display": "Ma***", "points": 3000},
    ]
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{"points": 100}]
    mock_sb.table.return_value.select.return_value.gt.return_value.execute.return_value.count = 42
    mocker.patch("supabase.create_client", return_value=mock_sb)
    resp = _client_free().get("/member/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "leaderboard" in data
    assert "my_rank" in data
