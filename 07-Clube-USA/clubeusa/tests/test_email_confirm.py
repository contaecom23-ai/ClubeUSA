"""
Tests para confirmação de email (Fase 0.1).
Cobre: request_email_confirmation e confirm_email em member_service.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import services.member_service  # must be imported before patching

MEMBER_ID = "00000000-0000-0000-0000-000000000001"
TOKEN = "valid_token_abc123def456xyz789"


# ============================================================
#  request_email_confirmation
# ============================================================

def test_request_email_confirmation_success():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "encrypted_email_value", "email_confirmed_at": None}
    ]
    mock_sb.table().update().eq().execute.return_value.data = [{}]

    with patch("services.member_service._supabase", return_value=mock_sb), \
         patch("services.member_service.decrypt", return_value="user@example.com"), \
         patch.dict("os.environ", {"ENVIRONMENT": "development"}):

        token = services.member_service.request_email_confirmation(MEMBER_ID)

    assert isinstance(token, str)
    assert len(token) >= 20


def test_request_email_confirmation_no_email():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": None, "email_confirmed_at": None}
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        with pytest.raises(ValueError, match="Nenhum email"):
            services.member_service.request_email_confirmation(MEMBER_ID)


def test_request_email_confirmation_empty_email():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "", "email_confirmed_at": None}
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        with pytest.raises(ValueError, match="Nenhum email"):
            services.member_service.request_email_confirmation(MEMBER_ID)


def test_request_email_confirmation_already_confirmed():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"email_enc": "enc", "email_confirmed_at": "2024-01-01T00:00:00Z"}
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        with pytest.raises(ValueError, match="já confirmado"):
            services.member_service.request_email_confirmation(MEMBER_ID)


def test_request_email_confirmation_member_not_found():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []

    with patch("services.member_service._supabase", return_value=mock_sb):
        with pytest.raises(ValueError, match="não encontrado"):
            services.member_service.request_email_confirmation(MEMBER_ID)


# ============================================================
#  confirm_email
# ============================================================

def test_confirm_email_success():
    future = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": MEMBER_ID, "email_confirmation_token_expires": future, "email_confirmed_at": None}
    ]
    mock_sb.table().update().eq().execute.return_value.data = [{}]

    with patch("services.member_service._supabase", return_value=mock_sb), \
         patch("services.member_service._audit"):
        result = services.member_service.confirm_email(TOKEN)

    assert result is True
    mock_sb.table().update().eq().execute.assert_called_once()


def test_confirm_email_invalid_token():
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = []

    with patch("services.member_service._supabase", return_value=mock_sb):
        assert services.member_service.confirm_email("nonexistent_token_xyz") is False


def test_confirm_email_expired_token():
    past = (datetime.utcnow() - timedelta(hours=1)).isoformat()
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": MEMBER_ID, "email_confirmation_token_expires": past, "email_confirmed_at": None}
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        assert services.member_service.confirm_email(TOKEN) is False


def test_confirm_email_already_confirmed_is_idempotent():
    """Token já confirmado retorna True sem fazer update duplo."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {
            "id": MEMBER_ID,
            "email_confirmation_token_expires": None,
            "email_confirmed_at": "2024-01-01T10:00:00Z",
        }
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        assert services.member_service.confirm_email(TOKEN) is True

    mock_sb.table().update.assert_not_called()


def test_confirm_email_no_expires_field():
    """Token sem campo expires retorna False (dado corrompido)."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [
        {"id": MEMBER_ID, "email_confirmation_token_expires": None, "email_confirmed_at": None}
    ]

    with patch("services.member_service._supabase", return_value=mock_sb):
        assert services.member_service.confirm_email(TOKEN) is False
