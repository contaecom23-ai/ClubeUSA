# ============================================================
#  tests/test_email_verification.py — Clube USA
#  Testa o fluxo de confirmacao de email (Fase 0.1)
# ============================================================

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

os.environ.setdefault("SUPABASE_URL", "https://fake.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "fake_service_key")
os.environ.setdefault("ENCRYPTION_KEY", "A" * 32)
os.environ.setdefault("JWT_SECRET", "fake_jwt_secret")
os.environ.setdefault("APP_URL", "https://clubeusa.com")
os.environ["ENVIRONMENT"] = "test"


def _make_sb_mock(
    email_enc="encrypted_email",
    email_confirmed_at=None,
    token_record=None,
):
    sb = MagicMock()
    # members table
    m_result = MagicMock()
    m_result.data = [{
        "id": "member-uuid-123",
        "email_enc": email_enc,
        "email_confirmed_at": email_confirmed_at,
    }]
    sb.table.return_value.select.return_value.eq.return_value.execute.return_value = m_result

    # email_tokens table — delete then insert
    sb.table.return_value.delete.return_value.eq.return_value.is_.return_value.execute.return_value = MagicMock()
    insert_result = MagicMock()
    insert_result.data = [{"id": "token-uuid-456"}]
    sb.table.return_value.insert.return_value.execute.return_value = insert_result

    if token_record is not None:
        token_result = MagicMock()
        token_result.data = [token_record]
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = token_result

    return sb


# -----------------------------------------------------------------------
# request_email_verification
# -----------------------------------------------------------------------

class TestRequestEmailVerification:

    def test_generates_token_and_returns_dev_link(self):
        sb = _make_sb_mock(email_enc="encrypted_email@example.com")

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import request_email_verification
            result = request_email_verification("member-uuid-123")

        assert result["sent"] is True
        assert result["expires_in_hours"] == 24
        assert result["dev_link"] is not None
        assert "/auth/email/verify/" in result["dev_link"]

    def test_raises_if_no_email(self):
        sb = _make_sb_mock(email_enc=None)
        m_result = MagicMock()
        m_result.data = [{"id": "member-uuid-123", "email_enc": None, "email_confirmed_at": None}]
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = m_result

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import request_email_verification
            with pytest.raises(ValueError, match="Nenhum email cadastrado"):
                request_email_verification("member-uuid-123")

    def test_raises_if_member_not_found(self):
        sb = MagicMock()
        not_found = MagicMock()
        not_found.data = []
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = not_found

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import request_email_verification
            with pytest.raises(ValueError, match="Membro nao encontrado"):
                request_email_verification("nonexistent")

    def test_production_mode_no_dev_link(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        sb = _make_sb_mock(email_enc="encrypted_email@example.com")

        with patch("services.email_service._supabase", return_value=sb), \
             patch("services.email_service._send_verification_email") as mock_send:
            from services.email_service import request_email_verification
            result = request_email_verification("member-uuid-123")

        assert result["dev_link"] is None
        mock_send.assert_called_once()

        monkeypatch.setenv("ENVIRONMENT", "test")


# -----------------------------------------------------------------------
# verify_email_token
# -----------------------------------------------------------------------

class TestVerifyEmailToken:

    def _valid_token_record(self, offset_hours=23):
        expires = (datetime.now(timezone.utc) + timedelta(hours=offset_hours)).isoformat()
        return {
            "id":         "token-uuid-456",
            "member_id":  "member-uuid-123",
            "token":      "valid_token_abc",
            "expires_at": expires,
            "used_at":    None,
        }

    def test_confirms_email_for_valid_token(self):
        record = self._valid_token_record()
        sb = MagicMock()

        token_result = MagicMock()
        token_result.data = [record]
        update_result = MagicMock()
        update_result.data = [{"id": record["id"]}]

        # token lookup
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = token_result
        # update calls
        sb.table.return_value.update.return_value.eq.return_value.execute.return_value = update_result
        # audit insert
        sb.table.return_value.insert.return_value.execute.return_value = MagicMock()

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import verify_email_token
            result = verify_email_token("valid_token_abc")

        assert result["confirmed"] is True
        assert result["member_id"] == "member-uuid-123"

    def test_raises_for_unknown_token(self):
        sb = MagicMock()
        not_found = MagicMock()
        not_found.data = []
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = not_found

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import verify_email_token
            with pytest.raises(ValueError, match="Token invalido"):
                verify_email_token("bad_token")

    def test_raises_for_used_token(self):
        record = self._valid_token_record()
        record["used_at"] = datetime.now(timezone.utc).isoformat()

        sb = MagicMock()
        token_result = MagicMock()
        token_result.data = [record]
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = token_result

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import verify_email_token
            with pytest.raises(ValueError, match="ja utilizado"):
                verify_email_token("already_used_token")

    def test_raises_for_expired_token(self):
        record = self._valid_token_record(offset_hours=-1)  # expired 1h ago

        sb = MagicMock()
        token_result = MagicMock()
        token_result.data = [record]
        sb.table.return_value.select.return_value.eq.return_value.execute.return_value = token_result

        with patch("services.email_service._supabase", return_value=sb):
            from services.email_service import verify_email_token
            with pytest.raises(ValueError, match="expirado"):
                verify_email_token("expired_token")


# -----------------------------------------------------------------------
# profile field
# -----------------------------------------------------------------------

class TestProfileEmailConfirmed:
    """
    Testa que get_member_profile inclui email_confirmed corretamente.
    Mocka utils.security para evitar dependencia nativa de cryptography
    no ambiente de testes.
    """

    def _member_row(self, confirmed=False):
        return {
            "id":                "member-uuid-123",
            "name_enc":          None,
            "phone_enc":         "enc_phone",
            "email_enc":         "enc_email",
            "email_confirmed_at": "2026-10-01T10:00:00+00:00" if confirmed else None,
            "language":          "pt",
            "state":             "FL",
            "plan":              "free",
            "points":            100,
            "level":             "bronze",
            "categories":        ["all"],
            "referral_code":     "ABC12345",
            "referral_count":    0,
            "total_clicks":      0,
            "created_at":        "2026-09-01T00:00:00+00:00",
            "vip_expires_at":    None,
        }

    def _run_get_profile(self, row):
        """Helper que isola a importacao de member_service com mocks de segurança."""
        import sys
        import types

        # Cria mock de utils.security para evitar import de cryptography nativa
        fake_security = types.ModuleType("utils.security")
        fake_security.encrypt = lambda x: "enc_" + (x or "")
        fake_security.decrypt = lambda x: "decoded_value"
        fake_security.hash_pii = lambda x: "hash_" + (x or "")
        fake_security.hash_ip = lambda x: "ip_hash"
        fake_security.validate_phone = lambda x: x
        fake_security.validate_email = lambda x: x
        fake_security.sanitize = lambda x, n=100: x
        fake_security.generate_referral_code = lambda: "TESTCODE"
        fake_security.generate_utm = lambda a, b: "utm_test"
        fake_security.create_token = lambda *a, **kw: "fake_token"

        with patch.dict(sys.modules, {
            "utils.security": fake_security,
            "utils": types.ModuleType("utils"),
            "services.group_manager": MagicMock(),
        }):
            # Force fresh import
            if "services.member_service" in sys.modules:
                del sys.modules["services.member_service"]

            sb = MagicMock()
            sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [row]

            with patch("builtins.__import__", side_effect=lambda name, *a, **kw: (
                sb if name == "supabase" else __import__(name, *a, **kw)
            )):
                pass  # import happens inside the mock context below

            # Patch supabase at module level
            import importlib
            with patch.dict(sys.modules, {"services.group_manager": MagicMock()}):
                import services.member_service as ms
                ms._supabase = lambda: sb
                ms.decrypt = lambda x: "decoded_value"
                profile = ms.get_member_profile("member-uuid-123")

        return profile

    def test_email_confirmed_true_when_confirmed(self):
        row = self._member_row(confirmed=True)
        profile = self._run_get_profile(row)
        assert profile["email_confirmed"] is True

    def test_email_confirmed_false_when_not_confirmed(self):
        row = self._member_row(confirmed=False)
        profile = self._run_get_profile(row)
        assert profile["email_confirmed"] is False
