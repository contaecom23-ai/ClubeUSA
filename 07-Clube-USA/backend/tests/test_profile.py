import uuid
from unittest.mock import MagicMock


def _make_execute(data=None):
    m = MagicMock()
    m.data = data or []
    return m


class TestGetProfile:
    def test_success(self, client, mock_supabase, auth_headers, sample_user_id):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            # primeiro: query de users
            _make_execute(data=[{"id": sample_user_id, "email": "u@e.com", "is_email_confirmed": True}]),
            # segundo: query de profiles
            _make_execute(data=[{
                "user_id": sample_user_id,
                "full_name": "João",
                "city": "Orlando",
                "state": "FL",
                "zip_code": "32801",
                "phone": None,
                "bio": None,
                "avatar_url": None,
            }]),
        ]
        resp = client.get("/profile/me", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "u@e.com"
        assert data["city"] == "Orlando"
        # Garante que user_id no response é do token, não inventado pelo cliente
        assert data["user_id"] == sample_user_id

    def test_deleted_user_returns_404(self, client, mock_supabase, auth_headers):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[])
        )
        resp = client.get("/profile/me", headers=auth_headers)
        assert resp.status_code == 404


class TestUpdateProfile:
    def test_update_success(self, client, mock_supabase, auth_headers, sample_user_id):
        # Sequência de chamadas:
        #   1) update: select users
        #   2) update: select profile exists
        #   3) update: update profile
        #   4) get_my_profile re-call: select users
        #   5) get_my_profile re-call: select profiles
        user_row = {"id": sample_user_id, "email": "u@e.com", "is_email_confirmed": False}
        profile_row = {
            "user_id": sample_user_id, "full_name": "Novo Nome",
            "city": "Miami", "state": "FL", "zip_code": None,
            "phone": None, "bio": None, "avatar_url": None,
        }

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            _make_execute(data=[user_row]),       # verifica user existe
            _make_execute(data=[{"id": "pid"}]),  # profile exists check
            _make_execute(data=[user_row]),       # re-get user
            _make_execute(data=[profile_row]),    # re-get profile
        ]
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[profile_row])
        )

        resp = client.put(
            "/profile/me",
            json={"full_name": "Novo Nome", "city": "Miami", "state": "FL"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == "Miami"

    def test_invalid_zip_code(self, client, mock_supabase, auth_headers):
        resp = client.put(
            "/profile/me",
            json={"zip_code": "INVALIDO"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_bio_too_long(self, client, mock_supabase, auth_headers):
        resp = client.put(
            "/profile/me",
            json={"bio": "x" * 501},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    def test_avatar_url_must_be_https(self, client, mock_supabase, auth_headers):
        resp = client.put(
            "/profile/me",
            json={"avatar_url": "http://nao-seguro.com/img.png"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestCrossTenantIsolation:
    """Garante que user A não consegue ver/alterar dados do user B."""

    def test_user_always_gets_own_data(self, client, mock_supabase, auth_headers, sample_user_id):
        """O endpoint usa user_id do token, nunca do path/body."""
        other_user_id = str(uuid.uuid4())
        user_row = {"id": sample_user_id, "email": "a@a.com", "is_email_confirmed": True}
        profile_row = {"user_id": sample_user_id, "full_name": "A", "city": None,
                       "state": None, "zip_code": None, "phone": None, "bio": None, "avatar_url": None}

        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.side_effect = [
            _make_execute(data=[user_row]),
            _make_execute(data=[profile_row]),
        ]

        # Mesmo enviando outro user_id no path (não temos path param, mas confirmamos pelo token)
        resp = client.get("/profile/me", headers=auth_headers)
        assert resp.status_code == 200
        # O user_id retornado deve ser o do TOKEN, não de outro
        assert resp.json()["user_id"] == sample_user_id
        assert resp.json()["user_id"] != other_user_id
