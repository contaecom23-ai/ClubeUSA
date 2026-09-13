# tests/test_housing.py — Clube USA — Fase 1.5
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


@pytest.fixture
def mock_sb():
    with patch("services.housing_service._supabase") as mock:
        sb = MagicMock()
        mock.return_value = sb
        yield sb


def _make_listing(**kwargs):
    base = {
        "id": "housing-uuid-001",
        "title": "Quarto disponível em Orlando — perto do metrô",
        "description": "Quarto mobiliado em apartamento com 2 quartos, próximo ao metrô.",
        "listing_type": "room",
        "price_monthly": 700.00,
        "utilities_included": True,
        "location_city": "Orlando",
        "location_state": "FL",
        "zip_code": "32801",
        "bedrooms": 1,
        "bathrooms": 1.0,
        "gender_preference": "any",
        "pets_allowed": False,
        "move_in_date": "2026-10-01",
        "contact_email": None,
        "contact_phone": None,
        "contact_whatsapp": "+14071234567",
        "posted_by": None,
        "is_active": True,
        "expires_at": None,
        "created_at": "2026-09-13T10:00:00Z",
        "updated_at": "2026-09-13T10:00:00Z",
    }
    base.update(kwargs)
    return base


def _chain_list(mock_sb, data):
    """Monta a cadeia de chamadas para list_housing."""
    q = MagicMock()
    q.execute.return_value.data = data
    chain = mock_sb.table.return_value.select.return_value.eq.return_value
    chain.order.return_value.limit.return_value.offset.return_value.or_.return_value = q
    return q


# ── list_housing ──────────────────────────────────────────────

class TestListHousing:
    def test_returns_empty_when_no_listings(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.housing_service import list_housing
        assert list_housing() == []

    def test_returns_active_listings(self, mock_sb):
        _chain_list(mock_sb, [_make_listing()])
        from services.housing_service import list_housing
        result = list_housing()
        assert len(result) == 1
        assert result[0]["title"] == "Quarto disponível em Orlando — perto do metrô"

    def test_limit_capped_at_100(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.housing_service import list_housing
        list_housing(limit=9999)
        limit_call = mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit
        assert limit_call.call_args[0][0] == 100

    def test_ignores_unknown_listing_type_filter(self, mock_sb):
        _chain_list(mock_sb, [])
        from services.housing_service import list_housing
        result = list_housing(listing_type="spaceship")
        assert result == []


# ── get_housing ──────────────────────────────────────────────

class TestGetHousing:
    def _chain_get(self, mock_sb, data):
        q = MagicMock()
        q.execute.return_value.data = data
        mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value = q

    def test_returns_none_when_not_found(self, mock_sb):
        self._chain_get(mock_sb, [])
        from services.housing_service import get_housing
        assert get_housing("nonexistent") is None

    def test_returns_listing(self, mock_sb):
        self._chain_get(mock_sb, [_make_listing()])
        from services.housing_service import get_housing
        result = get_housing("housing-uuid-001")
        assert result is not None
        assert result["id"] == "housing-uuid-001"

    def test_expired_listing_returns_none(self, mock_sb):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self._chain_get(mock_sb, [_make_listing(expires_at=past)])
        from services.housing_service import get_housing
        assert get_housing("housing-uuid-001") is None

    def test_non_expired_listing_returned(self, mock_sb):
        future = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        self._chain_get(mock_sb, [_make_listing(expires_at=future)])
        from services.housing_service import get_housing
        result = get_housing("housing-uuid-001")
        assert result is not None


# ── create_housing ───────────────────────────────────────────

class TestCreateHousing:
    def _mock_insert(self, mock_sb, data):
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = data

    def test_creates_listing_successfully(self, mock_sb):
        self._mock_insert(mock_sb, [_make_listing()])
        from services.housing_service import create_housing
        result = create_housing(
            title="Quarto disponível em Orlando — perto do metrô",
            description="Quarto mobiliado em apartamento com 2 quartos, próximo ao metrô.",
            price_monthly=700.0,
        )
        assert result["id"] == "housing-uuid-001"
        mock_sb.table.return_value.insert.assert_called_once()

    def test_rejects_invalid_listing_type(self, mock_sb):
        from services.housing_service import create_housing
        with pytest.raises(ValueError, match="listing_type"):
            create_housing(
                title="Quarto X",
                description="Descrição longa o suficiente para criar listagem",
                listing_type="spaceship",
                price_monthly=500,
            )

    def test_rejects_invalid_gender_preference(self, mock_sb):
        from services.housing_service import create_housing
        with pytest.raises(ValueError, match="gender_preference"):
            create_housing(
                title="Quarto X",
                description="Descrição longa o suficiente para criar listagem",
                price_monthly=500,
                gender_preference="nonbinary_only",
            )

    def test_rejects_negative_price(self, mock_sb):
        from services.housing_service import create_housing
        with pytest.raises(ValueError, match="negativo"):
            create_housing(
                title="Quarto X",
                description="Descrição longa o suficiente para criar listagem",
                price_monthly=-100,
            )

    def test_raises_on_db_failure(self, mock_sb):
        self._mock_insert(mock_sb, [])
        from services.housing_service import create_housing
        with pytest.raises(RuntimeError, match="Falha"):
            create_housing(
                title="Quarto X",
                description="Descrição longa o suficiente para criar listagem",
                price_monthly=500,
            )

    def test_truncates_long_title(self, mock_sb):
        self._mock_insert(mock_sb, [_make_listing()])
        from services.housing_service import create_housing
        create_housing(
            title="A" * 300,
            description="Descrição longa o suficiente para criar listagem",
            price_monthly=500,
        )
        inserted = mock_sb.table.return_value.insert.call_args[0][0]
        assert len(inserted["title"]) == 200


# ── deactivate_housing ───────────────────────────────────────

class TestDeactivateHousing:
    def test_deactivates_listing(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [_make_listing(is_active=False)]
        from services.housing_service import deactivate_housing
        assert deactivate_housing("housing-uuid-001") is True

    def test_returns_false_for_missing_listing(self, mock_sb):
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = []
        from services.housing_service import deactivate_housing
        assert deactivate_housing("nonexistent") is False


# ── isolation: member_id never from client ───────────────────

class TestIsolation:
    def test_list_housing_does_not_expose_contact_info(self, mock_sb):
        """
        list_housing retorna apenas campos públicos — contact_email, contact_phone,
        contact_whatsapp e posted_by não são incluídos no select de listagem.
        Dados de contato só aparecem no get_housing (detail).
        """
        _chain_list(mock_sb, [])
        from services.housing_service import list_housing
        list_housing()
        select_call = mock_sb.table.return_value.select.call_args[0][0]
        assert "contact_email" not in select_call
        assert "contact_phone" not in select_call
        assert "contact_whatsapp" not in select_call
        assert "posted_by" not in select_call
