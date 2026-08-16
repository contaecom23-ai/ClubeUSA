import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

# ENCRYPTION_KEY e usado pelo rate_limit_middleware (hash_ip) em cada request.
# Nao ha .env neste ambiente de teste, entao definimos um valor dummy aqui.
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-dummy-value")

from fastapi.testclient import TestClient
from unittest.mock import MagicMock

def _client_with_paid_member(mocker):
    from main import app
    import deps
    app.dependency_overrides[deps.require_paid_plan] = lambda: {"sub": "m-1", "plan": "vip"}
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "m-1", "plan": "vip"}
    return TestClient(app)

def test_post_products_track_returns_201(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.create_tracked_product",
        return_value={"id": "tp-1", "title": "Echo Dot", "offers": []},
    )
    resp = client.post("/products/track", json={"url": "https://www.amazon.com/dp/B08N5WRWNW"})
    assert resp.status_code == 201
    assert resp.json()["id"] == "tp-1"

def test_post_products_track_returns_400_on_value_error(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.create_tracked_product",
        side_effect=ValueError("Link não reconhecido."),
    )
    resp = client.post("/products/track", json={"url": "https://google.com"})
    assert resp.status_code == 400

def test_get_products_track_lists_member_products(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch(
        "services.tracked_product_service.list_tracked_products",
        return_value=[{"id": "tp-1", "title": "Echo Dot"}],
    )
    resp = client.get("/products/track")
    assert resp.status_code == 200
    assert resp.json()[0]["id"] == "tp-1"

def test_delete_products_track_returns_204(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch("services.tracked_product_service.cancel_tracked_product", return_value=True)
    resp = client.delete("/products/track/tp-1")
    assert resp.status_code == 204

def test_delete_products_track_returns_404_when_not_found(mocker):
    client = _client_with_paid_member(mocker)
    mocker.patch("services.tracked_product_service.cancel_tracked_product", return_value=False)
    resp = client.delete("/products/track/tp-inexistente")
    assert resp.status_code == 404
