import uuid
from unittest.mock import MagicMock


def _make_execute(data=None, error=None):
    m = MagicMock()
    m.data = data or []
    m.error = error
    return m


def _setup_fresh_user(mock_db, user_id=None):
    """Configura mock para simular usuário inexistente no registro."""
    uid = user_id or str(uuid.uuid4())
    mock_db.table.return_value.select.return_value.eq.return_value.execute.return_value = (
        _make_execute(data=[])  # email não existe
    )
    mock_db.table.return_value.insert.return_value.execute.return_value = _make_execute(
        data=[{"id": uid}]
    )
    return uid


class TestRegister:
    def test_success(self, client, mock_supabase):
        uid = _setup_fresh_user(mock_supabase)
        resp = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "Senha@123", "full_name": "João Silva"},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_duplicate_email(self, client, mock_supabase):
        # Simula email já existente
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[{"id": str(uuid.uuid4())}])
        )
        resp = client.post(
            "/auth/register",
            json={"email": "dup@example.com", "password": "Senha@123", "full_name": "Dup"},
        )
        assert resp.status_code == 409

    def test_weak_password_too_short(self, client, mock_supabase):
        resp = client.post(
            "/auth/register",
            json={"email": "t@example.com", "password": "abc", "full_name": "Teste"},
        )
        assert resp.status_code == 422

    def test_password_no_number_or_special(self, client, mock_supabase):
        resp = client.post(
            "/auth/register",
            json={"email": "t@example.com", "password": "abcdefgh", "full_name": "Teste"},
        )
        assert resp.status_code == 422

    def test_invalid_email(self, client, mock_supabase):
        resp = client.post(
            "/auth/register",
            json={"email": "nao-e-email", "password": "Senha@123", "full_name": "Teste"},
        )
        assert resp.status_code == 422

    def test_empty_full_name(self, client, mock_supabase):
        resp = client.post(
            "/auth/register",
            json={"email": "t@example.com", "password": "Senha@123", "full_name": ""},
        )
        assert resp.status_code == 422


class TestConfirmEmail:
    def test_success(self, client, mock_supabase):
        uid = str(uuid.uuid4())
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(
                data=[{
                    "id": uid,
                    "is_email_confirmed": False,
                    "confirmation_token_expires_at": "2099-01-01T00:00:00+00:00",
                }]
            )
        )
        mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[{"id": uid}])
        )
        resp = client.get("/auth/confirm-email?token=valid_token_abc")
        assert resp.status_code == 200
        assert "confirmado" in resp.json()["message"]

    def test_invalid_token(self, client, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[])
        )
        resp = client.get("/auth/confirm-email?token=invalid_token")
        assert resp.status_code == 400

    def test_expired_token(self, client, mock_supabase):
        uid = str(uuid.uuid4())
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(
                data=[{
                    "id": uid,
                    "is_email_confirmed": False,
                    "confirmation_token_expires_at": "2000-01-01T00:00:00+00:00",
                }]
            )
        )
        resp = client.get("/auth/confirm-email?token=expired_token")
        assert resp.status_code == 400

    def test_already_confirmed(self, client, mock_supabase):
        uid = str(uuid.uuid4())
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(
                data=[{
                    "id": uid,
                    "is_email_confirmed": True,
                    "confirmation_token_expires_at": "2099-01-01T00:00:00+00:00",
                }]
            )
        )
        resp = client.get("/auth/confirm-email?token=valid_token")
        assert resp.status_code == 200
        assert "já confirmado" in resp.json()["message"]


class TestLogin:
    def test_success(self, client, mock_supabase):
        from auth_utils import hash_password
        uid = str(uuid.uuid4())
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[{"id": uid, "password_hash": hash_password("Senha@123")}])
        )
        resp = client.post("/auth/login", json={"email": "u@e.com", "password": "Senha@123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_wrong_password(self, client, mock_supabase):
        from auth_utils import hash_password
        uid = str(uuid.uuid4())
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[{"id": uid, "password_hash": hash_password("Senha@123")}])
        )
        resp = client.post("/auth/login", json={"email": "u@e.com", "password": "errada123!"})
        assert resp.status_code == 401

    def test_user_not_found(self, client, mock_supabase):
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = (
            _make_execute(data=[])
        )
        resp = client.post("/auth/login", json={"email": "nao@existe.com", "password": "Senha@123"})
        assert resp.status_code == 401


class TestJWTProtection:
    def test_no_token_returns_401(self, client):
        resp = client.get("/profile/me")
        assert resp.status_code == 403  # HTTPBearer retorna 403 se sem header

    def test_invalid_token_returns_401(self, client):
        resp = client.get("/profile/me", headers={"Authorization": "Bearer token_invalido"})
        assert resp.status_code == 401
