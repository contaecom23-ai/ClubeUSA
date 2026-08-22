"""Testes de propriedades de seguranca criticas:
- Todos os endpoints protegidos exigem autenticacao (401 sem token)
- Token invalido retorna 401
- Isolamento multi-tenant: membro A nao acessa dados de membro B
- Endpoints publicos funcionam sem token
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))
os.environ.setdefault("ENCRYPTION_KEY", "test-encryption-key-dummy-value-32b")
os.environ.setdefault("SECRET_KEY", "test-secret-key-dummy-value-for-jwt-32b")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("APP_URL", "https://clubeusa.com")

import pytest
from fastapi.testclient import TestClient


# Todos os endpoints que exigem autenticacao de membro
PROTECTED_MEMBER_ENDPOINTS = [
    ("GET",   "/member/profile"),
    ("PATCH", "/member/profile"),
    ("GET",   "/member/deals"),
    ("GET",   "/member/referral"),
    ("GET",   "/member/leaderboard"),
    ("POST",  "/member/click"),
    ("POST",  "/billing/subscribe"),
    ("POST",  "/billing/portal"),
]

# Endpoints publicos (sem autenticacao)
PUBLIC_ENDPOINTS = [
    ("GET", "/health"),
    ("GET", "/public/groups"),
]


@pytest.fixture
def client():
    from main import app
    app.dependency_overrides.clear()
    return TestClient(app)


@pytest.mark.parametrize("method,path", PROTECTED_MEMBER_ENDPOINTS)
def test_protected_endpoint_requires_auth(client, method, path):
    """Sem token: deve retornar 401, nao 200, 400, 404, 500."""
    resp = getattr(client, method.lower())(path)
    assert resp.status_code == 401, (
        f"{method} {path} deve exigir auth, retornou {resp.status_code}: {resp.text}"
    )


@pytest.mark.parametrize("method,path", PROTECTED_MEMBER_ENDPOINTS)
def test_protected_endpoint_rejects_invalid_token(client, method, path):
    """Token invalido deve retornar 401."""
    resp = getattr(client, method.lower())(
        path, headers={"Authorization": "Bearer token-invalido-qualquer-coisa"}
    )
    assert resp.status_code == 401, (
        f"{method} {path} deve rejeitar token invalido, retornou {resp.status_code}"
    )


@pytest.mark.parametrize("method,path", PUBLIC_ENDPOINTS)
def test_public_endpoint_no_auth_required(client, method, path):
    """Endpoints publicos devem responder sem token (nao 401)."""
    resp = getattr(client, method.lower())(path)
    assert resp.status_code != 401, (
        f"{method} {path} e publico mas exigiu auth: {resp.status_code}"
    )


def test_profile_uses_token_identity_not_url_param(mocker):
    """Isolamento multi-tenant: nao e possivel ver perfil de outro membro.
    O servidor usa o sub do token JWT, nunca um id fornecido pelo cliente.
    """
    from main import app
    import deps

    # Membro A autentica
    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "member-A", "plan": "free"}

    mock_get = mocker.patch(
        "services.member_service.get_member_profile",
        return_value={"id": "member-A", "name": "Alice"},
    )

    c = TestClient(app)
    resp = c.get("/member/profile")
    assert resp.status_code == 200

    # Servico foi chamado com o id de A (do token), nao com input do cliente
    mock_get.assert_called_once_with("member-A")

    # Nao e possivel passar um id diferente na URL — nao existe /member/profile/{id}
    resp_b = c.get("/member/profile/member-B")
    assert resp_b.status_code == 404  # rota nao existe

    app.dependency_overrides.clear()


def test_click_uses_token_member_id_not_body(mocker):
    """POST /member/click: o member_id para rastreio vem do token, nao do body.
    Um membro mal-intencionado nao pode atribuir cliques a outro membro.
    """
    from main import app
    import deps

    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "member-A", "plan": "free"}

    mock_sb = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"id": "d1", "affiliate_url": "https://amazon.com/dp/B001?tag=abc"}
    ]
    mocker.patch("supabase.create_client", return_value=mock_sb)
    mock_track = mocker.patch("services.member_service.track_click", return_value="utm-ok")

    c = TestClient(app)
    # Corpo nao tem member_id — ele nao existe no schema
    c.post("/member/click", json={"deal_id": "d1"})

    # track_click deve ter sido chamado com member_id = "member-A" (do token)
    call_kwargs = mock_track.call_args[1]
    assert call_kwargs["member_id"] == "member-A"

    app.dependency_overrides.clear()


def test_referral_endpoint_uses_token_sub(mocker):
    """GET /member/referral: retorna dados do membro do token, nao de outro."""
    from main import app
    import deps

    app.dependency_overrides[deps.get_current_member] = lambda: {"sub": "member-A", "plan": "free"}

    mock_sb = __import__("unittest.mock", fromlist=["MagicMock"]).MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
        {"referral_code": "AAA111", "referral_count": 2, "points": 400, "level": "member"}
    ]
    mock_sb.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    mocker.patch("supabase.create_client", return_value=mock_sb)

    c = TestClient(app)
    resp = c.get("/member/referral")
    assert resp.status_code == 200
    # O link de referral deve conter o codigo de A, nao de B
    assert "AAA111" in resp.json()["referral_link"]

    app.dependency_overrides.clear()
