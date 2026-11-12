"""
Fase 1.1 — Promoções/Achados
Cobre: submit, list, get, upvote, delete, IDOR, rate-limit, validação.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
os.environ.setdefault("ENCRYPTION_KEY",    "test-key-dummy-32chars-padding!!")
os.environ.setdefault("SUPABASE_URL",       "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("ADMIN_SECRET",       "admin-secret-test")

from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import pytest


# ============================================================
#  HELPERS
# ============================================================

def _make_promo(id="p-1", submitted_by="m-1", status="approved", upvotes=0):
    return {
        "id": id, "submitted_by": submitted_by,
        "title": "Frango $1.99/lb no Walmart",
        "description": None, "store_name": "Walmart",
        "url": None, "price_now": 1.99, "price_was": None,
        "zip_code": "10001", "state": "NY", "category": "grocery",
        "status": status, "upvotes": upvotes, "expires_at": None,
        "created_at": "2026-09-26T10:00:00Z", "updated_at": "2026-09-26T10:00:00Z",
    }


def _client():
    from main import app
    import deps
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-1", "plan": "free"}
    app.dependency_overrides[deps.require_admin] = lambda: None
    return TestClient(app)


def _sb_empty():
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    return sb


# ============================================================
#  SUBMIT
# ============================================================

def test_submit_valid_promotion(mocker):
    client = _client()
    sb = MagicMock()
    # count check: 0 submissions today
    sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(count=0, data=[])
    # insert result
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "p-new"}])
    mocker.patch("routers.promotions._sb", return_value=sb)

    resp = client.post("/promotions", json={
        "title": "Frango $1.99/lb — promoção do dia no Walmart",
        "store_name": "Walmart",
        "category": "grocery",
        "zip_code": "10001",
        "price_now": 1.99,
    })
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"


def test_submit_missing_title_returns_422():
    client = _client()
    resp = client.post("/promotions", json={"store_name": "Walmart", "category": "grocery"})
    assert resp.status_code == 422


def test_submit_title_too_short_returns_422():
    client = _client()
    resp = client.post("/promotions", json={
        "title": "Hi", "store_name": "Walmart", "category": "grocery"
    })
    assert resp.status_code == 422


def test_submit_invalid_category_returns_422():
    client = _client()
    resp = client.post("/promotions", json={
        "title": "Frango bem barato hoje no mercado",
        "store_name": "Walmart",
        "category": "invalid_cat",
    })
    assert resp.status_code == 422


def test_submit_invalid_zip_returns_422():
    client = _client()
    resp = client.post("/promotions", json={
        "title": "Frango bem barato hoje aqui",
        "store_name": "Walmart",
        "category": "grocery",
        "zip_code": "abc-invalid",
    })
    assert resp.status_code == 422


def test_submit_invalid_url_returns_422():
    client = _client()
    resp = client.post("/promotions", json={
        "title": "Frango bem barato hoje aqui",
        "store_name": "Walmart",
        "category": "grocery",
        "url": "not-a-url",
    })
    assert resp.status_code == 422


def test_submit_negative_price_returns_422():
    client = _client()
    resp = client.post("/promotions", json={
        "title": "Frango bem barato hoje mesmo",
        "store_name": "Walmart",
        "category": "grocery",
        "price_now": -1.0,
    })
    assert resp.status_code == 422


def test_submit_daily_limit_returns_429(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = MagicMock(count=5, data=[])
    mocker.patch("routers.promotions._sb", return_value=sb)

    resp = client.post("/promotions", json={
        "title": "Frango $1.99/lb — mais barato impossível",
        "store_name": "Walmart",
        "category": "grocery",
    })
    assert resp.status_code == 429


# ============================================================
#  LIST / GET
# ============================================================

def test_list_promotions_returns_200(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.order.return_value.order.return_value.range.return_value.execute.return_value = MagicMock(data=[_make_promo()])
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.get("/promotions")
    assert resp.status_code == 200
    assert isinstance(resp.json()["promotions"], list)


def test_get_own_pending_promotion_visible(mocker):
    """Membro vê a própria promoção pendente."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="m-1", status="pending")]
    )
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.get("/promotions/p-1")
    assert resp.status_code == 200


def test_get_other_pending_returns_404(mocker):
    """IDOR: membro não vê promoção pendente de outro — retorna 404 (não 403)."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="other-member", status="pending")]
    )
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.get("/promotions/p-other")
    assert resp.status_code == 404


def test_get_nonexistent_returns_404(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.get("/promotions/nonexistent")
    assert resp.status_code == 404


# ============================================================
#  UPVOTE
# ============================================================

def test_upvote_returns_updated_count(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="other-member", upvotes=3)]
    )
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{}])
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    mocker.patch("routers.promotions._sb", return_value=sb)

    resp = client.post("/promotions/p-1/upvote")
    assert resp.status_code == 200
    assert resp.json()["upvotes"] == 4


def test_upvote_own_promotion_returns_400(mocker):
    """Não pode votar na própria promoção."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="m-1", upvotes=0)]
    )
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.post("/promotions/p-1/upvote")
    assert resp.status_code == 400


def test_upvote_nonexistent_returns_404(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.post("/promotions/nonexistent/upvote")
    assert resp.status_code == 404


def test_upvote_duplicate_returns_409(mocker):
    """Duplo voto retorna 409."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="other-member", upvotes=1)]
    )
    # Simulate unique constraint violation on insert
    sb.table.return_value.insert.return_value.execute.side_effect = Exception("duplicate key")
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.post("/promotions/p-1/upvote")
    assert resp.status_code == 409


# ============================================================
#  DELETE
# ============================================================

def test_delete_own_pending_returns_204(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="m-1", status="pending")]
    )
    sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.delete("/promotions/p-1")
    assert resp.status_code == 204


def test_delete_other_member_returns_404(mocker):
    """IDOR: não pode deletar promoção de outro — 404 (não 403)."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="other-member", status="pending")]
    )
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.delete("/promotions/p-other")
    assert resp.status_code == 404


def test_delete_approved_promotion_returns_400(mocker):
    """Não pode deletar promoção já aprovada."""
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[_make_promo(submitted_by="m-1", status="approved")]
    )
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.delete("/promotions/p-1")
    assert resp.status_code == 400


def test_delete_nonexistent_returns_404(mocker):
    client = _client()
    sb = MagicMock()
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
    mocker.patch("routers.promotions._sb", return_value=sb)
    resp = client.delete("/promotions/nonexistent")
    assert resp.status_code == 404


# ============================================================
#  UNAUTHENTICATED
# ============================================================

def test_list_unauthenticated_returns_401():
    from main import app
    import deps
    app.dependency_overrides = {}  # remove overrides
    c = TestClient(app)
    resp = c.get("/promotions")
    assert resp.status_code == 401
    # restore for other tests
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-1", "plan": "free"}
    app.dependency_overrides[deps.require_admin] = lambda: None
