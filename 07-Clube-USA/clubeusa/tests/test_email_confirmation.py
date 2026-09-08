# tests/test_email_confirmation.py — Clube USA
# Testa o fluxo de confirmacao de email (Fase 0.1)

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

# ============================================================
#  FIXTURES
# ============================================================

MEMBER_ID = "aaaaaaaa-0000-0000-0000-000000000001"
OTHER_ID  = "bbbbbbbb-0000-0000-0000-000000000002"


def _make_supabase_mock(
    email_enc="enc:test@example.com",
    email_confirmed=False,
    has_member=True,
    token_record=None,
    insert_ok=True,
):
    """Cria mock do Supabase configuravel para os cenarios de teste."""
    sb = MagicMock()

    # Mock de members.select
    member_data = [{
        "id":              MEMBER_ID,
        "email_enc":       email_enc,
        "email_hash":      "hash_email",
        "email_confirmed": email_confirmed,
    }] if has_member else []

    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=member_data
    )
    sb.table.return_value.select.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(
        data=[token_record] if token_record else []
    )
    sb.table.return_value.delete.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
    sb.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "tok-id"}] if insert_ok else []
    )
    sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    sb.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(data=[])

    return sb


# ============================================================
#  send_confirmation_email
# ============================================================

class TestSendConfirmationEmail:
    def test_raises_if_no_email(self):
        sb = _make_supabase_mock(email_enc="")
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789",
                                     "ENVIRONMENT": "development"}):
            from services.email_confirmation_service import send_confirmation_email
            with pytest.raises(ValueError, match="Nenhum email"):
                send_confirmation_email(MEMBER_ID)

    def test_raises_if_member_not_found(self):
        sb = _make_supabase_mock(has_member=False)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789",
                                     "ENVIRONMENT": "development"}):
            from services.email_confirmation_service import send_confirmation_email
            with pytest.raises(ValueError, match="nao encontrado"):
                send_confirmation_email(MEMBER_ID)

    def test_returns_already_confirmed_if_done(self):
        sb = _make_supabase_mock(email_enc="some_enc", email_confirmed=True)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789",
                                     "ENVIRONMENT": "development"}):
            from services.email_confirmation_service import send_confirmation_email
            result = send_confirmation_email(MEMBER_ID)
            assert result.get("already_confirmed") is True

    def test_dev_returns_link_not_sent(self):
        sb = _make_supabase_mock(email_enc="some_enc", email_confirmed=False)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch("services.email_confirmation_service.decrypt", return_value="test@example.com"), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789",
                                     "ENVIRONMENT": "development",
                                     "APP_URL": "http://localhost:8000"}):
            from services import email_confirmation_service as svc
            svc._APP_URL = "http://localhost:8000"
            result = svc.send_confirmation_email(MEMBER_ID)
            assert result["sent"] is False
            assert "dev_link" in result
            assert "/auth/email/confirm/" in result["dev_link"]
            assert "te**" in result["email_masked"] or "test" in result["email_masked"]


# ============================================================
#  verify_confirmation_token
# ============================================================

class TestVerifyConfirmationToken:
    def _valid_token_record(self, raw_token: str) -> dict:
        expires = (datetime.now(timezone.utc) + timedelta(hours=23)).isoformat()
        return {
            "id":         "tok-id",
            "member_id":  MEMBER_ID,
            "token_hash": hashlib.sha256(raw_token.encode()).hexdigest(),
            "expires_at": expires,
            "used_at":    None,
        }

    def test_invalid_empty_token(self):
        with patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x"}):
            from services.email_confirmation_service import verify_confirmation_token
            with pytest.raises(ValueError, match="invalido"):
                verify_confirmation_token("")

    def test_token_not_found(self):
        sb = _make_supabase_mock(token_record=None)
        raw_token = secrets.token_urlsafe(32)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x"}):
            from services.email_confirmation_service import verify_confirmation_token
            with pytest.raises(ValueError, match="invalido ou ja utilizado"):
                verify_confirmation_token(raw_token)

    def test_expired_token(self):
        raw_token = secrets.token_urlsafe(32)
        expired_record = {
            "id":         "tok-id",
            "member_id":  MEMBER_ID,
            "token_hash": hashlib.sha256(raw_token.encode()).hexdigest(),
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
            "used_at":    None,
        }
        sb = _make_supabase_mock(token_record=expired_record)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x"}):
            from services.email_confirmation_service import verify_confirmation_token
            with pytest.raises(ValueError, match="expirado"):
                verify_confirmation_token(raw_token)

    def test_valid_token_confirms_email(self):
        raw_token = secrets.token_urlsafe(32)
        record = self._valid_token_record(raw_token)
        sb = _make_supabase_mock(token_record=record)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x"}):
            from services.email_confirmation_service import verify_confirmation_token
            result = verify_confirmation_token(raw_token)
            assert result["confirmed"] is True
            assert result["member_id"] == MEMBER_ID


# ============================================================
#  add_or_update_email
# ============================================================

class TestAddOrUpdateEmail:
    def test_rejects_email_taken_by_other_member(self):
        sb = MagicMock()
        # email_hash ja existe em outro membro
        sb.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(
            data=[{"id": OTHER_ID}]
        )
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789"}):
            from services.email_confirmation_service import add_or_update_email
            with pytest.raises(ValueError, match="ja esta cadastrado"):
                add_or_update_email(MEMBER_ID, "taken@example.com")

    def test_rejects_invalid_email_format(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(data=[])
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789"}):
            from services.email_confirmation_service import add_or_update_email
            with pytest.raises(ValueError, match="Email invalido"):
                add_or_update_email(MEMBER_ID, "not-an-email")

    def test_updates_email_and_resets_confirmation(self):
        sb = MagicMock()
        sb.table.return_value.select.return_value.eq.return_value.neq.return_value.execute.return_value = MagicMock(data=[])
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
        sb.table.return_value.delete.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock(data=[])
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x",
                                     "ENCRYPTION_KEY": "test_key_32chars_padded_123456789"}):
            from services.email_confirmation_service import add_or_update_email
            result = add_or_update_email(MEMBER_ID, "new@example.com")
            assert result["email_updated"] is True
            assert "email_masked" in result


# ============================================================
#  Isolamento multi-tenant: outro membro NAO pode confirmar token alheio
# ============================================================

class TestMultiTenantIsolation:
    def test_token_belongs_to_correct_member(self):
        """Cada token esta vinculado a um member_id; a query filtra por token_hash — nao por member_id no input."""
        raw_token = secrets.token_urlsafe(32)
        record = {
            "id":         "tok-id",
            "member_id":  MEMBER_ID,     # dono real do token
            "token_hash": hashlib.sha256(raw_token.encode()).hexdigest(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=10)).isoformat(),
            "used_at":    None,
        }
        sb = _make_supabase_mock(token_record=record)
        with patch("services.email_confirmation_service._supabase", return_value=sb), \
             patch.dict(os.environ, {"SUPABASE_URL": "x", "SUPABASE_SERVICE_KEY": "x"}):
            from services.email_confirmation_service import verify_confirmation_token
            result = verify_confirmation_token(raw_token)
            # O membro confirmado e sempre o do token, nunca um input externo
            assert result["member_id"] == MEMBER_ID
