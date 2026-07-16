"""Testes de integração das rotas de usuário — DB mockado."""
import pytest

from security import create_access_token


def _set_select(mock_db, data):
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value.data = data


def _set_update(mock_db, data=None):
    mock_db.table.return_value.update.return_value.eq.return_value.execute.return_value.data = data or []


def _valid_user_row():
    return {
        "id": "user-123",
        "email": "maria@example.com",
        "name": "Maria Silva",
        "phone": "+1 305 555-0100",
        "state": "FL",
        "city": "Miami",
        "zip_code": "33101",
        "email_confirmed_at": "2026-07-01T00:00:00+00:00",
        "referral_code": None,
        "created_at": "2026-07-01T00:00:00+00:00",
    }


def _auth_header(user_id: str = "user-123") -> dict:
    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


class TestGetProfile:
    def test_success(self, client, mock_db):
        _set_select(mock_db, [_valid_user_row()])

        r = client.get("/api/users/me", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == "user-123"
        assert data["email"] == "maria@example.com"
        assert data["name"] == "Maria Silva"
        assert data["state"] == "FL"
        assert data["email_confirmed"] is True

    def test_no_auth_returns_401(self, client, mock_db):
        r = client.get("/api/users/me")
        assert r.status_code in (401, 403)

    def test_invalid_token_returns_401(self, client, mock_db):
        r = client.get("/api/users/me", headers={"Authorization": "Bearer token.invalido.aqui"})
        assert r.status_code == 401

    def test_user_not_in_db_returns_404(self, client, mock_db):
        _set_select(mock_db, [])  # usuário sumiu do banco após emissão do token

        r = client.get("/api/users/me", headers=_auth_header())
        assert r.status_code == 404


class TestUpdateProfile:
    def test_update_name(self, client, mock_db):
        updated = {**_valid_user_row(), "name": "Maria Santos"}
        _set_update(mock_db)
        _set_select(mock_db, [updated])

        r = client.put("/api/users/me", json={"name": "Maria Santos"}, headers=_auth_header())
        assert r.status_code == 200
        assert r.json()["name"] == "Maria Santos"

    def test_blank_name_rejected(self, client, mock_db):
        r = client.put("/api/users/me", json={"name": "   "}, headers=_auth_header())
        assert r.status_code == 422

    def test_no_auth_returns_401(self, client, mock_db):
        r = client.put("/api/users/me", json={"name": "Alguém"})
        assert r.status_code in (401, 403)

    def test_empty_body_returns_current_profile(self, client, mock_db):
        _set_select(mock_db, [_valid_user_row()])

        r = client.put("/api/users/me", json={}, headers=_auth_header())
        assert r.status_code == 200
        assert r.json()["id"] == "user-123"

    def test_cannot_change_email_via_update(self, client, mock_db):
        # email não está em UpdateProfileRequest — deve ser ignorado
        _set_select(mock_db, [_valid_user_row()])

        r = client.put("/api/users/me", json={"email": "hacker@evil.com"}, headers=_auth_header())
        # Pydantic ignora campos extras — retorna 200 com o perfil original
        assert r.status_code == 200
        assert r.json()["email"] == "maria@example.com"


class TestRegistrationValidity:
    def _validity_row(self, confirmed=True, state=None, city=None, zip_code=None):
        return [{
            "email_confirmed_at": "2026-07-01T00:00:00+00:00" if confirmed else None,
            "state": state,
            "city": city,
            "zip_code": zip_code,
        }]

    def test_valid_confirmed_with_zip(self, client, mock_db):
        _set_select(mock_db, self._validity_row(confirmed=True, zip_code="33101"))

        r = client.get("/api/users/me/validity", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["is_valid"] is True
        assert data["email_confirmed"] is True
        assert data["has_location"] is True
        assert data["required_actions"] == []

    def test_valid_confirmed_with_state_city(self, client, mock_db):
        _set_select(mock_db, self._validity_row(confirmed=True, state="FL", city="Miami"))

        r = client.get("/api/users/me/validity", headers=_auth_header())
        assert r.status_code == 200
        assert r.json()["is_valid"] is True

    def test_invalid_not_confirmed(self, client, mock_db):
        _set_select(mock_db, self._validity_row(confirmed=False, zip_code="33101"))

        r = client.get("/api/users/me/validity", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["is_valid"] is False
        assert data["email_confirmed"] is False
        assert "required_actions" in data
        assert any("email" in a.lower() for a in data["required_actions"])

    def test_invalid_confirmed_no_location(self, client, mock_db):
        _set_select(mock_db, self._validity_row(confirmed=True))

        r = client.get("/api/users/me/validity", headers=_auth_header())
        assert r.status_code == 200
        data = r.json()
        assert data["is_valid"] is False
        assert data["has_location"] is False
        assert any("localização" in a.lower() or "cep" in a.lower() or "cidade" in a.lower()
                   for a in data["required_actions"])

    def test_no_auth_returns_401(self, client, mock_db):
        r = client.get("/api/users/me/validity")
        assert r.status_code in (401, 403)

    def test_user_not_found_returns_404(self, client, mock_db):
        _set_select(mock_db, [])
        r = client.get("/api/users/me/validity", headers=_auth_header())
        assert r.status_code == 404
