"""
Testes para rotas de autenticação.
Cobre: validação de input, fluxo de auth, JWT, isolamento multi-tenant.
"""
import pytest

from tests.conftest import TEST_USER_ID, TEST_USER_ID_B, make_token

# ─── /health ──────────────────────────────────────────────────────────────────


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ─── POST /api/v1/auth/register ───────────────────────────────────────────────


def test_register_success(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "novo@example.com", "password": "Senha123", "full_name": "João"},
    )
    assert r.status_code == 201
    assert "email" in r.json()["message"].lower()


def test_register_missing_fields(client):
    c, _ = client
    r = c.post("/api/v1/auth/register", json={"email": "x@x.com"})
    assert r.status_code == 422


def test_register_invalid_email(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "nao-e-email", "password": "Senha123", "full_name": "João"},
    )
    assert r.status_code == 422


def test_register_weak_password_too_short(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "abc", "full_name": "João"},
    )
    assert r.status_code == 422
    assert "8" in r.text


def test_register_weak_password_no_number(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "abcdefgh", "full_name": "João"},
    )
    assert r.status_code == 422
    assert "número" in r.text


def test_register_weak_password_no_letter(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "12345678", "full_name": "João"},
    )
    assert r.status_code == 422
    assert "letra" in r.text


def test_register_name_too_short(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "Senha123", "full_name": "J"},
    )
    assert r.status_code == 422


def test_register_name_too_long(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "Senha123", "full_name": "J" * 101},
    )
    assert r.status_code == 422


def test_register_supabase_error_returns_400(client, mocker):
    c, sb = client
    sb.auth.sign_up.side_effect = Exception("User already registered")
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "Senha123", "full_name": "João"},
    )
    assert r.status_code == 400


def test_register_profile_error_cleans_up_auth_user(client, mocker):
    """Garante que usuário órfão é removido se o insert do perfil falhar."""
    c, sb = client
    sb.table.return_value.insert.return_value.execute.side_effect = Exception("DB error")
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "Senha123", "full_name": "João"},
    )
    assert r.status_code == 500
    sb.auth.admin.delete_user.assert_called_once_with(TEST_USER_ID)


# ─── POST /api/v1/auth/login ──────────────────────────────────────────────────


def test_login_success(client):
    c, _ = client
    r = c.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "Senha123"},
    )
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    c, sb = client
    sb.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
    r = c.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "errada"},
    )
    assert r.status_code == 401
    # Não deve revelar se foi email ou senha — mensagem genérica
    assert "incorretos" in r.json()["detail"]


def test_login_missing_fields(client):
    c, _ = client
    r = c.post("/api/v1/auth/login", json={"email": "x@x.com"})
    assert r.status_code == 422


# ─── GET /api/v1/auth/me ──────────────────────────────────────────────────────


def test_me_authenticated(client):
    c, _ = client
    token = make_token(TEST_USER_ID)
    r = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    data = r.json()
    assert data["user_id"] == TEST_USER_ID
    assert "full_name" in data
    assert "email" in data


def test_me_no_token(client):
    c, _ = client
    r = c.get("/api/v1/auth/me")
    assert r.status_code == 403  # HTTPBearer retorna 403 sem header


def test_me_expired_token(client):
    c, _ = client
    token = make_token(TEST_USER_ID, expired=True)
    r = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_me_malformed_token(client):
    c, _ = client
    r = c.get("/api/v1/auth/me", headers={"Authorization": "Bearer nao.e.jwt"})
    assert r.status_code == 401


def test_me_profile_not_found(client, mocker):
    """404 para usuário autenticado mas sem perfil (edge case de dados)."""
    c, sb = client
    no_data = mocker.MagicMock()
    no_data.data = None
    (
        sb.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value
    ) = no_data
    token = make_token(TEST_USER_ID)
    r = c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404


# ─── Isolamento multi-tenant ──────────────────────────────────────────────────


def test_me_user_id_comes_from_jwt_not_body(client):
    """
    /me ignora qualquer user_id no body/query.
    O user_id vem SEMPRE do JWT validado.
    """
    c, sb = client
    token_a = make_token(TEST_USER_ID)
    # Mesmo passando user_id_b na query string (inventado), o endpoint usa o do JWT
    r = c.get(
        f"/api/v1/auth/me?user_id={TEST_USER_ID_B}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert r.status_code == 200
    # A query ao Supabase usa TEST_USER_ID (do JWT), não TEST_USER_ID_B
    call_args = sb.table.return_value.select.return_value.eq.call_args
    assert call_args[0][1] == TEST_USER_ID


# ─── PUT /api/v1/auth/me ──────────────────────────────────────────────────────


def test_update_profile_success(client):
    c, _ = client
    token = make_token(TEST_USER_ID)
    r = c.put(
        "/api/v1/auth/me",
        json={"full_name": "Novo Nome"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["full_name"] == "Novo Nome"


def test_update_profile_unauthenticated(client):
    c, _ = client
    r = c.put("/api/v1/auth/me", json={"full_name": "Teste"})
    assert r.status_code == 403


# ─── POST /api/v1/auth/logout ─────────────────────────────────────────────────


def test_logout_authenticated(client):
    c, _ = client
    token = make_token(TEST_USER_ID)
    r = c.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204


def test_logout_unauthenticated(client):
    c, _ = client
    r = c.post("/api/v1/auth/logout")
    assert r.status_code == 403


# ─── Security headers ─────────────────────────────────────────────────────────


def test_security_headers_present_on_every_response(client):
    c, _ = client
    r = c.get("/health")
    assert r.headers.get("X-Content-Type-Options") == "nosniff"
    assert r.headers.get("X-Frame-Options") == "DENY"
    assert r.headers.get("X-XSS-Protection") == "1; mode=block"
    assert r.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert r.headers.get("Permissions-Policy") == "geolocation=(), microphone=()"


def test_hsts_absent_outside_production(client):
    c, _ = client
    r = c.get("/health")
    assert "Strict-Transport-Security" not in r.headers


def test_docs_accessible_in_development(client):
    c, _ = client
    r = c.get("/api/docs")
    assert r.status_code == 200
