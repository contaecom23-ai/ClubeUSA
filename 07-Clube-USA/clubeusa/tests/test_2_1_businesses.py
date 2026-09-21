# tests/test_2_1_businesses.py — Fase 2.1: local business subscription
import pytest
from unittest.mock import patch, MagicMock


# ── BusinessRegisterRequest validation ───────────────────────────────────────

def _make_register_body(**kwargs):
    from routers.businesses import BusinessRegisterRequest
    defaults = {"phone": "+13055550001", "name": "Test Business", "category": "restaurant"}
    defaults.update(kwargs)
    return BusinessRegisterRequest(**defaults)


def test_register_name_too_short():
    from routers.businesses import BusinessRegisterRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="menos 2"):
        BusinessRegisterRequest(phone="+13055550001", name="X", category="restaurant")


def test_register_name_strips_and_truncates():
    body = _make_register_body(name="  My Bakery  ")
    assert body.name == "My Bakery"


def test_register_invalid_category():
    from routers.businesses import BusinessRegisterRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="Categoria inválida"):
        BusinessRegisterRequest(phone="+13055550001", name="Test", category="unicorn")


def test_register_valid_categories():
    from routers.businesses import _VALID_CATEGORIES
    for cat in _VALID_CATEGORIES:
        body = _make_register_body(category=cat)
        assert body.category == cat


def test_register_zip_invalid():
    from routers.businesses import BusinessRegisterRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="ZIP"):
        BusinessRegisterRequest(phone="+13055550001", name="Test", category="retail", zip_code="ABC12")


def test_register_zip_valid():
    body = _make_register_body(zip_code="90210")
    assert body.zip_code == "90210"


def test_register_website_auto_prefix():
    body = _make_register_body(website="example.com")
    assert body.website == "https://example.com"


def test_register_website_already_https():
    body = _make_register_body(website="https://example.com")
    assert body.website == "https://example.com"


def test_register_description_truncated_at_500():
    body = _make_register_body(description="A" * 600)
    assert len(body.description) == 500


# ── BusinessSubscribeRequest validation ──────────────────────────────────────

def test_subscribe_invalid_plan():
    from routers.businesses import BusinessSubscribeRequest
    from pydantic import ValidationError
    with pytest.raises(ValidationError, match="inválido"):
        BusinessSubscribeRequest(plan="enterprise")


def test_subscribe_valid_plans():
    from routers.businesses import BusinessSubscribeRequest
    for plan in ("basic", "premium"):
        req = BusinessSubscribeRequest(plan=plan)
        assert req.plan == plan


# ── security.py: create_business_token ───────────────────────────────────────

def test_create_business_token_contains_role():
    import os
    os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-minimum-len!")
    from utils.security import create_business_token, verify_token
    token = create_business_token("biz-001", "basic")
    payload = verify_token(token)
    assert payload is not None
    assert payload["role"] == "business"
    assert payload["sub"] == "biz-001"
    assert payload["plan"] == "basic"


def test_member_token_has_no_role():
    import os
    os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-minimum-len!")
    from utils.security import create_token, verify_token
    token = create_token("member-001", "free")
    payload = verify_token(token)
    assert payload is not None
    assert payload.get("role") is None


# ── deps.py: get_current_business ────────────────────────────────────────────

def test_get_current_business_rejects_member_token():
    import os
    os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-minimum-len!")
    from utils.security import create_token
    from deps import get_current_business
    from fastapi import HTTPException
    token = create_token("member-001", "free")
    with pytest.raises(HTTPException) as exc_info:
        get_current_business(authorization=f"Bearer {token}")
    assert exc_info.value.status_code == 401


def test_get_current_business_accepts_business_token():
    import os
    os.environ.setdefault("JWT_SECRET", "test-secret-32-chars-minimum-len!")
    from utils.security import create_business_token
    from deps import get_current_business
    token = create_business_token("biz-001", "basic")
    payload = get_current_business(authorization=f"Bearer {token}")
    assert payload["sub"] == "biz-001"
    assert payload["role"] == "business"


def test_get_current_business_rejects_missing_token():
    from deps import get_current_business
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc_info:
        get_current_business(authorization=None)
    assert exc_info.value.status_code == 401


# ── Public listing: filter logic ─────────────────────────────────────────────

def test_public_listing_category_validation():
    """Category filter only passes through valid categories (no injection)."""
    from routers.businesses import _VALID_CATEGORIES
    assert "restaurant" in _VALID_CATEGORIES
    assert "DROP TABLE businesses" not in _VALID_CATEGORIES


# ── handle_business_checkout_completed ───────────────────────────────────────

def test_checkout_completed_updates_business_plan():
    mock_sb = MagicMock()
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

    with patch("routers.businesses._sb", return_value=mock_sb):
        from routers.businesses import handle_business_checkout_completed
        handle_business_checkout_completed({
            "metadata": {"business_id": "biz-001", "plan": "premium", "role": "business"},
            "customer": "cus_test",
        })

    # Verify update was called with correct plan
    update_call = mock_sb.table.return_value.update.call_args
    assert update_call is not None
    called_data = update_call[0][0]
    assert called_data["plan"] == "premium"
    assert called_data["status"] == "active"


def test_checkout_completed_noop_without_business_id():
    """Should do nothing if business_id is missing from metadata."""
    mock_sb = MagicMock()
    with patch("routers.businesses._sb", return_value=mock_sb):
        from routers.businesses import handle_business_checkout_completed
        handle_business_checkout_completed({"metadata": {}, "customer": "cus_test"})
    mock_sb.table.assert_not_called()
