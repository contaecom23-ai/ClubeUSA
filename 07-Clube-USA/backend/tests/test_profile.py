"""Testes de perfil: GET, PATCH e isolamento multi-tenant (cross-tenant → 404)."""
from unittest.mock import MagicMock
from tests.conftest import PROFILE_A, PROFILE_B, USER_A_ID, USER_B_ID


def _setup_profile_fetch(mock_supabase, profile_data):
    """Configura mock para retornar um perfil na busca por id."""
    chain = MagicMock()
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = profile_data
    return chain


# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------
def test_get_profile_sem_token(client):
    resp = client.get("/profile")
    assert resp.status_code in (401, 403)


def test_get_profile_sucesso(client, mock_supabase, token_a):
    _setup_profile_fetch(mock_supabase, PROFILE_A)
    resp = client.get("/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == USER_A_ID
    assert data["full_name"] == "Ana Souza"

    # Confirma que a query filtrou pelo user_id do token, não de body/query
    call_args = mock_supabase.table.return_value.select.return_value.eq.call_args
    assert call_args[0] == ("id", USER_A_ID)


def test_get_profile_nao_encontrado(client, mock_supabase, token_a):
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
    resp = client.get("/profile", headers={"Authorization": f"Bearer {token_a}"})
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /profile
# ---------------------------------------------------------------------------
def test_patch_profile_sucesso(client, mock_supabase, token_a):
    updated = {**PROFILE_A, "city": "Tampa"}
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated]
    resp = client.patch(
        "/profile",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"city": "Tampa"},
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Tampa"

    # Confirma filtro por user_id do token
    eq_call = mock_supabase.table.return_value.update.return_value.eq.call_args
    assert eq_call[0] == ("id", USER_A_ID)


def test_patch_profile_sem_campos(client, mock_supabase, token_a):
    resp = client.patch(
        "/profile",
        headers={"Authorization": f"Bearer {token_a}"},
        json={},
    )
    assert resp.status_code == 400


def test_patch_profile_campo_proibido_ignorado(client, mock_supabase, token_a):
    """Campos não-atualizáveis (ex: referral_code) são ignorados silenciosamente."""
    updated = {**PROFILE_A}
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [updated]
    resp = client.patch(
        "/profile",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"full_name": "Ana Nova", "referral_code": "hackeado"},
    )
    assert resp.status_code == 200
    # Verifica que referral_code não foi passado ao banco
    update_call = mock_supabase.table.return_value.update.call_args
    update_payload = update_call[0][0]
    assert "referral_code" not in update_payload
    assert update_payload.get("full_name") == "Ana Nova"


# ---------------------------------------------------------------------------
# Isolamento multi-tenant: usuário A não acessa perfil de B
# ---------------------------------------------------------------------------
def test_cross_tenant_get_retorna_perfil_proprio(client, mock_supabase, token_a):
    """Mesmo que um atacante tente adivinhar outro user_id, a query sempre
    filtra pelo user_id extraído do JWT — não do request."""
    # Mock retorna dados de A (correto — filtro sempre por user_id do token)
    mock_supabase.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = PROFILE_A

    # Token de A tenta acessar /profile?user_id=B (parâmetro ignorado)
    resp = client.get(
        "/profile",
        headers={"Authorization": f"Bearer {token_a}"},
        params={"user_id": USER_B_ID},  # deve ser completamente ignorado
    )
    assert resp.status_code == 200
    # Retorna dados de A, não de B
    assert resp.json()["id"] == USER_A_ID

    # Confirma que a query filtrou por A, não por B
    eq_call = mock_supabase.table.return_value.select.return_value.eq.call_args
    assert eq_call[0] == ("id", USER_A_ID)
