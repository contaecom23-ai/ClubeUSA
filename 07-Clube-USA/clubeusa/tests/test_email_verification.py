"""
Tests for services/email_verification_service.py — Clube USA
Fase 0.1: email confirmation flow
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta, timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _future(hours=24):
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _past(hours=1):
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _table_mock():
    """Returns a fresh MagicMock configured for Supabase table chaining."""
    m = MagicMock()
    m.select.return_value = m
    m.eq.return_value = m
    m.gte.return_value = m
    m.is_.return_value = m
    m.update.return_value = m
    m.insert.return_value = m
    m.delete.return_value = m
    m.execute.return_value = MagicMock(data=[], count=0)
    return m


def _make_sb(members_mock=None, ev_tokens_mock=None, audit_mock=None):
    """
    Returns a mock Supabase client with per-table routing via side_effect.
    """
    sb = MagicMock()

    _tables = {
        "members":                    members_mock or _table_mock(),
        "email_verification_tokens":  ev_tokens_mock or _table_mock(),
        "audit_logs":                 audit_mock or _table_mock(),
    }

    def _table(name):
        return _tables.get(name, _table_mock())

    sb.table.side_effect = _table
    sb.rpc.return_value.execute.return_value = MagicMock()
    return sb


# ---------------------------------------------------------------------------
# request_email_verification
# ---------------------------------------------------------------------------

class TestRequestEmailVerification:

    def _member_table(self, data, count=0):
        t = _table_mock()
        t.execute.return_value = MagicMock(data=data, count=count)
        return t

    def _evtoken_table(self, count=0):
        t = _table_mock()
        # For rate-limit count query
        t.execute.return_value = MagicMock(data=[], count=count)
        return t

    def test_member_not_found_raises(self, mocker):
        members_t = self._member_table(data=[])
        sb = _make_sb(members_mock=members_t)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import request_email_verification
        with pytest.raises(ValueError, match="nao encontrado"):
            request_email_verification("m1")

    def test_no_email_raises(self, mocker):
        members_t = self._member_table(
            data=[{"id": "m1", "email_enc": None, "email_verified": False}]
        )
        sb = _make_sb(members_mock=members_t)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import request_email_verification
        with pytest.raises(ValueError, match="Nenhum email"):
            request_email_verification("m1")

    def test_already_verified_raises(self, mocker):
        members_t = self._member_table(
            data=[{"id": "m1", "email_enc": "enc", "email_verified": True}]
        )
        sb = _make_sb(members_mock=members_t)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import request_email_verification
        with pytest.raises(ValueError, match="ja confirmado"):
            request_email_verification("m1")

    def test_rate_limit_raises(self, mocker):
        members_t = self._member_table(
            data=[{"id": "m1", "email_enc": "enc", "email_verified": False}]
        )
        evt = self._evtoken_table(count=3)
        sb = _make_sb(members_mock=members_t, ev_tokens_mock=evt)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import request_email_verification
        with pytest.raises(ValueError, match="Limite"):
            request_email_verification("m1")

    def test_success_returns_message(self, mocker):
        members_t = self._member_table(
            data=[{"id": "m1", "email_enc": "enc_email", "email_verified": False}]
        )
        evt = self._evtoken_table(count=0)
        sb = _make_sb(members_mock=members_t, ev_tokens_mock=evt)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)
        mocker.patch("utils.security.decrypt", return_value="user@example.com")
        mocker.patch("services.email_verification_service._send_verification_email")

        from services.email_verification_service import request_email_verification
        result = request_email_verification("m1")

        assert "message" in result
        assert result["expires_in_hours"] == 24


# ---------------------------------------------------------------------------
# confirm_email_verification
# ---------------------------------------------------------------------------

class TestConfirmEmailVerification:

    def _evtoken_table_with_record(self, record):
        t = _table_mock()
        t.execute.return_value = MagicMock(data=[record] if record else [])
        return t

    def _members_table_verified(self, verified: bool):
        t = _table_mock()
        t.execute.return_value = MagicMock(data=[{"email_verified": verified}])
        return t

    def test_empty_token_raises(self):
        from services.email_verification_service import confirm_email_verification
        with pytest.raises(ValueError, match="invalido"):
            confirm_email_verification("")

    def test_token_too_long_raises(self):
        from services.email_verification_service import confirm_email_verification
        with pytest.raises(ValueError, match="invalido"):
            confirm_email_verification("x" * 65)

    def test_token_not_found_raises(self, mocker):
        evt = self._evtoken_table_with_record(None)
        sb = _make_sb(ev_tokens_mock=evt)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import confirm_email_verification
        with pytest.raises(ValueError, match="invalido"):
            confirm_email_verification("nosuchtoken")

    def test_already_used_raises(self, mocker):
        evt = self._evtoken_table_with_record({
            "id": "t1", "member_id": "m1", "token": "tok",
            "expires_at": _future(24), "used_at": _past(1),
        })
        sb = _make_sb(ev_tokens_mock=evt)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import confirm_email_verification
        with pytest.raises(ValueError, match="ja utilizado"):
            confirm_email_verification("tok")

    def test_expired_token_raises(self, mocker):
        evt = self._evtoken_table_with_record({
            "id": "t1", "member_id": "m1", "token": "tok",
            "expires_at": _past(1), "used_at": None,
        })
        sb = _make_sb(ev_tokens_mock=evt)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import confirm_email_verification
        with pytest.raises(ValueError, match="expirado"):
            confirm_email_verification("tok")

    def test_valid_token_confirms_email(self, mocker):
        evt = self._evtoken_table_with_record({
            "id": "t1", "member_id": "m1", "token": "validtoken",
            "expires_at": _future(24), "used_at": None,
        })
        members_t = self._members_table_verified(False)
        sb = _make_sb(ev_tokens_mock=evt, members_mock=members_t)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import confirm_email_verification
        result = confirm_email_verification("validtoken")

        assert result["already_verified"] is False
        assert result["points_awarded"] == 100
        assert "sucesso" in result["message"].lower()

    def test_already_verified_idempotent(self, mocker):
        evt = self._evtoken_table_with_record({
            "id": "t1", "member_id": "m1", "token": "validtoken",
            "expires_at": _future(24), "used_at": None,
        })
        members_t = self._members_table_verified(True)
        sb = _make_sb(ev_tokens_mock=evt, members_mock=members_t)
        mocker.patch("services.email_verification_service._supabase", return_value=sb)

        from services.email_verification_service import confirm_email_verification
        result = confirm_email_verification("validtoken")

        assert result["already_verified"] is True
