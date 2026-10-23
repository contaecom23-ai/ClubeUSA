"""
test_analytics.py — Fase 0.3 + 0.4

Testa analytics_service de forma isolada com mocks do Supabase.
"""

import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# analytics_service.track — nunca lança exceção
# ---------------------------------------------------------------------------

def test_track_silences_exception():
    """track() não deve propagar erros — analytics failure ≠ request failure."""
    with patch("services.analytics_service.create_client") as mock_client:
        mock_client.side_effect = Exception("Supabase indisponível")
        from services.analytics_service import track
        track("user.registered", member_id="uuid-1")  # não lança


def test_track_inserts_event():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_sb = MagicMock()
        mock_client.return_value = mock_sb
        mock_sb.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": 1}])

        from services.analytics_service import track
        import importlib
        import services.analytics_service as svc
        importlib.reload(svc)

        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            svc.track("user.login", member_id="uuid-1", properties={"plan": "free"})

        mock_sb.table.assert_called_with("analytics_events")
        call_args = mock_sb.table.return_value.insert.call_args[0][0]
        assert call_args["event_type"] == "user.login"
        assert call_args["member_id"] == "uuid-1"
        assert call_args["properties"] == {"plan": "free"}


# ---------------------------------------------------------------------------
# get_validation_status — lógica sem dependência externa
# ---------------------------------------------------------------------------

def _make_sb_mock(email_hash=None, email_confirmed=False, clicks=0, analytics_count=0):
    mock_sb = MagicMock()

    # members table
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"email_hash": email_hash, "email_confirmed": email_confirmed, "created_at": "2026-01-01"}]
    )

    # clicks count
    clicks_mock = MagicMock(count=clicks)
    analytics_mock = MagicMock(count=analytics_count)

    def table_side_effect(name):
        t = MagicMock()
        if name == "members":
            t.select.return_value.eq.return_value.execute.return_value = MagicMock(
                data=[{"email_hash": email_hash, "email_confirmed": email_confirmed, "created_at": "2026-01-01"}]
            )
        elif name == "clicks":
            t.select.return_value.eq.return_value.execute.return_value = clicks_mock
        elif name == "analytics_events":
            t.select.return_value.eq.return_value.in_.return_value.execute.return_value = analytics_mock
        return t

    mock_sb.table.side_effect = table_side_effect
    return mock_sb


def test_validation_status_no_email_no_action():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_client.return_value = _make_sb_mock(email_hash=None, email_confirmed=False, clicks=0)
        from services.analytics_service import get_validation_status
        import importlib
        import services.analytics_service as svc
        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            result = svc.get_validation_status("uuid-1")
        assert result["is_valid"] is False
        assert result["has_real_action"] is False


def test_validation_status_with_click_no_email():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_client.return_value = _make_sb_mock(email_hash=None, email_confirmed=False, clicks=1)
        import services.analytics_service as svc
        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            result = svc.get_validation_status("uuid-1")
        # Sem email, critério só é ação real
        assert result["is_valid"] is True
        assert result["has_real_action"] is True


def test_validation_status_email_not_confirmed():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_client.return_value = _make_sb_mock(
            email_hash="abc", email_confirmed=False, clicks=2
        )
        import services.analytics_service as svc
        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            result = svc.get_validation_status("uuid-1")
        # Tem ação real, mas email não confirmado → inválido
        assert result["is_valid"] is False
        assert "Email" in result["reason"]


def test_validation_status_email_confirmed_with_action():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_client.return_value = _make_sb_mock(
            email_hash="abc", email_confirmed=True, clicks=1
        )
        import services.analytics_service as svc
        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            result = svc.get_validation_status("uuid-1")
        assert result["is_valid"] is True
        assert result["email_confirmed"] is True


def test_validation_status_member_not_found():
    with patch("services.analytics_service.create_client") as mock_client:
        mock_sb = MagicMock()
        mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        mock_client.return_value = mock_sb
        import services.analytics_service as svc
        with patch.dict("os.environ", {"SUPABASE_URL": "https://x.supabase.co", "SUPABASE_SERVICE_KEY": "key"}):
            result = svc.get_validation_status("uuid-nao-existe")
        assert result["is_valid"] is False
