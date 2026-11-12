# tests/test_valid_registration.py
# Testes para Fase 0.4: antifraude (unitarios) + endpoint /members/me/valid-status
import importlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from services.antifraude import is_disposable_email, validate_email_for_registration


# ---------------------------------------------------------------------------
#  Fixtures do endpoint (Supabase mockado por membro)
# ---------------------------------------------------------------------------

_MEMBERS = {
    "mem-ok": {
        "email_confirmed": True, "is_disposable_email": False,
        "total_clicks": 3, "referral_count": 0,
    },
    "mem-unconfirmed": {
        "email_confirmed": False, "is_disposable_email": False,
        "total_clicks": 0, "referral_count": 0,
    },
}


def _sb_mock():
    sb = MagicMock()

    def _table(_name):
        q = MagicMock()
        q.select.return_value = q
        q.is_.return_value = q
        q.maybe_single.return_value = q

        def _eq(_col, val):
            q._member_id = val
            return q

        def _execute():
            res = MagicMock()
            res.data = _MEMBERS.get(getattr(q, "_member_id", None))
            return res

        q.eq.side_effect = _eq
        q.execute.side_effect = _execute
        return q

    sb.table.side_effect = _table
    return sb


@pytest.fixture()
def client():
    with patch("supabase.create_client", side_effect=lambda *a, **k: _sb_mock()):
        import routers.valid_registration as vr
        importlib.reload(vr)  # rebinding de create_client sob o patch
        import api.main as m
        importlib.reload(m)
        with TestClient(m.app, raise_server_exceptions=False) as c:
            yield c


@pytest.fixture()
def valid_member_token():
    from utils.security import create_token
    return create_token("mem-ok")


@pytest.fixture()
def unconfirmed_member_token():
    from utils.security import create_token
    return create_token("mem-unconfirmed")


class TestIsDisposableEmail:
    def test_known_disposable_domains(self):
        assert is_disposable_email("test@mailinator.com") is True
        assert is_disposable_email("user@yopmail.com") is True
        assert is_disposable_email("x@guerrillamail.com") is True
        assert is_disposable_email("a@10minutemail.com") is True
        assert is_disposable_email("foo@trashmail.com") is True
        assert is_disposable_email("foo@temp-mail.org") is True

    def test_legitimate_domains(self):
        assert is_disposable_email("user@gmail.com") is False
        assert is_disposable_email("user@hotmail.com") is False
        assert is_disposable_email("user@yahoo.com") is False
        assert is_disposable_email("user@outlook.com") is False
        assert is_disposable_email("user@empresa.com.br") is False

    def test_case_insensitive(self):
        assert is_disposable_email("user@MAILINATOR.COM") is True
        assert is_disposable_email("user@YopMail.com") is True

    def test_invalid_input(self):
        assert is_disposable_email("") is False
        assert is_disposable_email("notanemail") is False
        assert is_disposable_email(None) is False

    def test_subdomain_not_blocked(self):
        # Subdominios nao bloqueados (conservador: evitar falso positivo)
        assert is_disposable_email("user@mail.gmail.com") is False


class TestValidateEmailForRegistration:
    def test_disposable_email_rejected(self):
        ok, err = validate_email_for_registration("test@mailinator.com")
        assert ok is False
        assert err is not None
        assert "descartavel" in err.lower() or "temporario" in err.lower()

    def test_valid_email_accepted(self):
        ok, err = validate_email_for_registration("usuario@gmail.com")
        assert ok is True
        assert err is None

    def test_empty_email_rejected(self):
        ok, err = validate_email_for_registration("")
        assert ok is False

    def test_no_at_sign_rejected(self):
        ok, err = validate_email_for_registration("invalido.com")
        assert ok is False

    def test_too_long_rejected(self):
        ok, err = validate_email_for_registration("a" * 310 + "@gmail.com")
        assert ok is False


class TestRegisterRejectsDisposable:
    def test_disposable_email_422(self, client):
        resp = client.post("/auth/register", json={
            "phone": "+15551234567",
            "name": "Teste",
            "email": "qualquer@mailinator.com",
            "language": "pt",
        })
        assert resp.status_code == 422
        assert "descartaveis" in resp.json()["detail"]


class TestValidStatusEndpoint:
    """GET /members/me/valid-status com Supabase mockado."""

    def test_unauthenticated_returns_401(self, client):
        resp = client.get("/members/me/valid-status")
        assert resp.status_code == 401

    def test_valid_member_returns_valid_true(self, client, valid_member_token):
        resp = client.get(
            "/members/me/valid-status",
            headers={"Authorization": f"Bearer {valid_member_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["email_confirmed"] is True
        assert data["has_real_action"] is True
        assert data["is_disposable_email"] is False
        assert data["blocking_reason"] is None

    def test_unconfirmed_email_returns_valid_false(self, client, unconfirmed_member_token):
        resp = client.get(
            "/members/me/valid-status",
            headers={"Authorization": f"Bearer {unconfirmed_member_token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["email_confirmed"] is False
        assert "blocking_reason" in data
