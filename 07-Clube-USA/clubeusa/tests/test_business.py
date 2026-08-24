"""
tests/test_business.py — Testes unitarios para Phase 2.1 (Business Directory)
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException


class TestBusinessRegisterSchema:
    def _make(self, **kwargs):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
        from routers.business import BusinessRegister
        return BusinessRegister(**kwargs)

    def _base(self):
        return dict(name="Casa Brasileira", category="restaurant", zip_code="90001")

    def test_zip_strips_dashes(self):
        b = self._make(**{**self._base(), "zip_code": "90-001"})
        assert b.zip_code == "90001"

    def test_zip_valid_5_digits(self):
        b = self._make(**{**self._base(), "zip_code": "10001"})
        assert b.zip_code == "10001"

    def test_zip_invalid_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(**{**self._base(), "zip_code": "123"})

    def test_name_too_short_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(**{**self._base(), "name": "A"})

    def test_name_too_long_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(**{**self._base(), "name": "A" * 101})

    def test_invalid_category_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(**{**self._base(), "category": "invalid_cat"})

    def test_website_adds_https(self):
        b = self._make(**{**self._base(), "website": "example.com"})
        assert b.website == "https://example.com"

    def test_description_too_long_raises(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make(**{**self._base(), "description": "x" * 1001})

    def test_owner_id_not_in_schema(self):
        from routers.business import BusinessRegister
        assert "owner_id" not in BusinessRegister.model_fields


class TestBusinessUpdateSchema:
    def _make_update(self):
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
        from routers.business import BusinessUpdate
        return BusinessUpdate

    def test_plan_not_in_schema(self):
        BusinessUpdate = self._make_update()
        assert "plan" not in BusinessUpdate.model_fields

    def test_owner_id_not_in_schema(self):
        BusinessUpdate = self._make_update()
        assert "owner_id" not in BusinessUpdate.model_fields


def test_list_businesses_no_auth_required():
    """GET /business/directory nao requer token."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

    mock_sb = MagicMock()
    mock_query = MagicMock()
    mock_sb.table.return_value.select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.order.return_value = mock_query
    mock_query.limit.return_value = mock_query
    mock_query.execute.return_value = MagicMock(data=[
        {"id": "abc", "name": "Restaurante Brasil", "plan": "premium", "category": "restaurant"}
    ])

    with patch("routers.business._get_supabase", return_value=mock_sb):
        from routers.business import list_businesses
        import asyncio
        result = asyncio.run(list_businesses())

    assert "businesses" in result
    assert len(result["businesses"]) == 1


def test_get_business_for_owner_raises_404_for_wrong_owner():
    """_get_business_for_owner levanta 404 quando nao encontra — nunca 403 (nao vaza existencia)."""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))
    from routers.business import _get_business_for_owner

    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    with pytest.raises(HTTPException) as exc_info:
        _get_business_for_owner(mock_sb, "other-owner-uuid")

    assert exc_info.value.status_code == 404
