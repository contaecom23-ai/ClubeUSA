# tests/test_email_confirm.py — Fase 0.1: confirmação de email
#
# Cobertura:
#   - Token armazenado como hash (nunca em texto puro)
#   - Dev mode retorna dev_token
#   - Email duplicado levanta ValueError
#   - Token válido confirma email e retorna member_id
#   - Token expirado levanta ValueError
#   - Token já usado levanta ValueError
#   - Token desconhecido levanta ValueError
#   - Isolamento: token pertence ao member_id do registro, nunca de input externo
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest


def _sha256(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _make_sb_mock(select_data=None, conflict_data=None):
    """Helper para montar mock do Supabase com comportamento padrão."""
    mock_sb = MagicMock()

    # .select().eq().neq().execute() → sem conflito por padrão
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .neq.return_value
        .execute.return_value
        .data
    ) = conflict_data or []

    # .select().eq().execute() → dados do token
    (
        mock_sb.table.return_value
        .select.return_value
        .eq.return_value
        .execute.return_value
        .data
    ) = select_data or []

    # Mutações genéricas
    mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = None
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{"id": "tok-1"}]

    return mock_sb


# ============================================================
#  request_email_verification
# ============================================================

class TestRequestEmailVerification:

    def test_token_stored_as_hash_not_plaintext(self):
        """O token enviado ao usuário NUNCA é salvo em texto puro."""
        stored_inserts = []

        mock_sb = MagicMock()
        (
            mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .neq.return_value
            .execute.return_value
            .data
        ) = []
        mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = None
        mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{}]

        def capture(data):
            stored_inserts.append(data)
            m = MagicMock()
            m.execute.return_value.data = [data]
            return m

        mock_sb.table.return_value.insert.side_effect = capture

        with (
            patch("services.email_service._supabase", return_value=mock_sb),
            patch("services.email_service._send_email"),
            patch("utils.security.validate_email", return_value="test@example.com"),
            patch("utils.security.hash_pii", return_value="h_email"),
            patch("utils.security.encrypt", return_value="enc_email"),
            patch.dict("os.environ", {"ENVIRONMENT": "production", "APP_URL": "https://clubeusa.com"}),
        ):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            result = svc.request_email_verification("mem-1", "test@example.com")

        assert result["sent"] is True
        token_inserts = [i for i in stored_inserts if "token_hash" in i]
        assert len(token_inserts) == 1
        th = token_inserts[0]["token_hash"]
        # SHA-256 hex = 64 chars
        assert len(th) == 64
        # Não contém o token cru (que seria urlsafe, ~43 chars)
        assert "/" not in th and "+" not in th  # base64url chars absent in hex

    def test_dev_mode_returns_dev_token(self):
        """Em desenvolvimento, a resposta inclui dev_token para testes."""
        mock_sb = _make_sb_mock()

        with (
            patch("services.email_service._supabase", return_value=mock_sb),
            patch("utils.security.validate_email", return_value="dev@example.com"),
            patch("utils.security.hash_pii", return_value="h_dev"),
            patch("utils.security.encrypt", return_value="enc_dev"),
            patch.dict("os.environ", {"ENVIRONMENT": "development", "APP_URL": "http://localhost:8000"}),
        ):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            result = svc.request_email_verification("mem-dev", "dev@example.com")

        assert result["sent"] is True
        assert "dev_token" in result
        assert len(result["dev_token"]) > 10

    def test_duplicate_email_raises(self):
        """Email já em uso por outro membro levanta ValueError."""
        mock_sb = _make_sb_mock(conflict_data=[{"id": "other-member"}])

        with (
            patch("services.email_service._supabase", return_value=mock_sb),
            patch("utils.security.validate_email", return_value="dup@example.com"),
            patch("utils.security.hash_pii", return_value="h_dup"),
            patch("utils.security.encrypt", return_value="enc_dup"),
        ):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            with pytest.raises(ValueError, match="já está cadastrado"):
                svc.request_email_verification("mem-new", "dup@example.com")

    def test_same_member_can_update_email(self):
        """Membro pode reenviar confirmação para o mesmo email (sem conflito)."""
        mock_sb = _make_sb_mock(conflict_data=[])  # sem conflito

        with (
            patch("services.email_service._supabase", return_value=mock_sb),
            patch("utils.security.validate_email", return_value="me@example.com"),
            patch("utils.security.hash_pii", return_value="h_me"),
            patch("utils.security.encrypt", return_value="enc_me"),
            patch.dict("os.environ", {"ENVIRONMENT": "development"}),
        ):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            result = svc.request_email_verification("mem-same", "me@example.com")

        assert result["sent"] is True


# ============================================================
#  confirm_email_token
# ============================================================

class TestConfirmEmailToken:

    def _valid_record(self, token: str, member_id: str = "mem-abc") -> dict:
        return {
            "id":         "tok-1",
            "member_id":  member_id,
            "token_hash": _sha256(token),
            "used":       False,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }

    def test_valid_token_confirms_email(self):
        token = secrets.token_urlsafe(32)
        record = self._valid_record(token)
        mock_sb = _make_sb_mock(select_data=[record])

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            result = svc.confirm_email_token(token)

        assert result["confirmed"] is True
        assert result["member_id"] == "mem-abc"

    def test_expired_token_raises(self):
        token = secrets.token_urlsafe(32)
        record = {
            "id":         "tok-exp",
            "member_id":  "mem-x",
            "token_hash": _sha256(token),
            "used":       False,
            "expires_at": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
        }
        mock_sb = _make_sb_mock(select_data=[record])

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            with pytest.raises(ValueError, match="[Ee]xpirado"):
                svc.confirm_email_token(token)

    def test_used_token_raises(self):
        token = secrets.token_urlsafe(32)
        record = {
            "id":         "tok-used",
            "member_id":  "mem-y",
            "token_hash": _sha256(token),
            "used":       True,
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }
        mock_sb = _make_sb_mock(select_data=[record])

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            with pytest.raises(ValueError, match="já utilizado"):
                svc.confirm_email_token(token)

    def test_unknown_token_raises(self):
        mock_sb = _make_sb_mock(select_data=[])

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            with pytest.raises(ValueError, match="inválido"):
                svc.confirm_email_token("totally-unknown-token")

    def test_result_uses_stored_member_id_not_external_input(self):
        """
        Isolamento: o member_id retornado vem do registro do token,
        nunca de um parâmetro externo — garante que membro B não confirma
        email de membro A.
        """
        token = secrets.token_urlsafe(32)
        member_a = "mem-a-owner"
        record = self._valid_record(token, member_id=member_a)
        mock_sb = _make_sb_mock(select_data=[record])

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            result = svc.confirm_email_token(token)

        # O resultado sempre reflete o membro dono do token
        assert result["member_id"] == member_a

    def test_token_marked_used_before_db_confirm(self):
        """
        O token é marcado como used ANTES do UPDATE em members,
        evitando race condition em requisições paralelas.
        Verifica a ordem das chamadas ao Supabase.
        """
        token = secrets.token_urlsafe(32)
        record = self._valid_record(token)
        call_order = []

        mock_sb = MagicMock()
        (
            mock_sb.table.return_value
            .select.return_value
            .eq.return_value
            .execute.return_value
            .data
        ) = [record]

        original_update = mock_sb.table.return_value.update

        def track_update(data):
            call_order.append(list(data.keys()))
            m = MagicMock()
            m.eq.return_value.execute.return_value.data = [{}]
            return m

        mock_sb.table.return_value.update.side_effect = track_update
        mock_sb.table.return_value.insert.return_value.execute.return_value.data = [{}]
        mock_sb.table.return_value.delete.return_value.eq.return_value.execute.return_value = None

        with patch("services.email_service._supabase", return_value=mock_sb):
            import importlib, services.email_service as svc
            importlib.reload(svc)
            svc.confirm_email_token(token)

        # Primeira chamada update deve ser {used: True}, segunda {email_confirmed: True}
        assert call_order[0] == ["used"]
        assert call_order[1] == ["email_confirmed"]
