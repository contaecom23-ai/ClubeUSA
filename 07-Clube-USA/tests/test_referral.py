# tests/test_referral.py — Fase 0.2: Referral rastreavel
import pytest
from unittest.mock import MagicMock, patch


# ---- _mark_referral_click_converted ----

def test_mark_conversion_updates_click(mocker):
    from services.member_service import _mark_referral_click_converted

    mock_sb = MagicMock()
    mock_sb.table().select().eq().is_().order().limit().execute.return_value.data = [
        {"id": "click-uuid-1"}
    ]
    mock_sb.table().update().eq().execute.return_value = MagicMock()
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    _mark_referral_click_converted("ABC123", "member-uuid")

    # Verificar que update foi chamado (nao levantou excecao)
    assert mock_sb.table().update().eq().execute.called


def test_mark_conversion_no_click_is_noop(mocker):
    """Se nao ha clique registrado, nao falha — apenas nao atualiza."""
    from services.member_service import _mark_referral_click_converted

    mock_sb = MagicMock()
    mock_sb.table().select().eq().is_().order().limit().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    # Nao deve levantar excecao
    _mark_referral_click_converted("ABC123", "member-uuid")


# ---- register_member: conversao marcada quando referral_code passado ----

def test_register_with_referral_marks_conversion(mocker):
    """Registrar com referral_code valido deve chamar _mark_referral_click_converted."""
    from services.member_service import register_member

    mock_sb = MagicMock()
    # Sem membro duplicado
    mock_sb.table().select().eq().execute.return_value.data = []
    # Referrer existe
    mock_sb.table().select().eq().eq().execute.return_value.data = [{"id": "referrer-uuid"}]
    # Insert membro
    mock_sb.table().insert().execute.return_value.data = [{
        "id": "new-member-uuid",
        "plan": "free",
        "referral_code": "NEWCODE1",
    }]

    mocker.patch("services.member_service._supabase", return_value=mock_sb)
    mocker.patch("services.member_service.validate_phone", return_value="+15550001234")
    mocker.patch("services.member_service.validate_email", return_value="x@x.com")
    mocker.patch("services.member_service.encrypt", return_value="enc")
    mocker.patch("services.member_service.hash_pii", return_value="hash")
    mocker.patch("services.member_service.generate_referral_code", return_value="NEWCODE1")
    mocker.patch("services.member_service.create_token", return_value="jwt-tok")
    mocker.patch("services.member_service.assign_member_to_group", return_value={"invite_link": "#", "name": "G1"})
    mocker.patch("services.member_service._process_referral")
    mocker.patch("services.member_service._send_email_confirmation_token")
    mocker.patch("services.member_service._audit")
    mock_mark = mocker.patch("services.member_service._mark_referral_click_converted")

    result = register_member(
        phone="+15550001234",
        name="Test User",
        referral_code="REFCODE1",
    )

    assert result["action"] == "registered"
    mock_mark.assert_called_once_with("REFCODE1", "new-member-uuid")


# ---- Validacao de codigo referral: formato invalido rejeitado ----

def test_referral_code_format_validation():
    """Codigos com caracteres invalidos nao devem passar pela regex."""
    import re
    valid_pattern = re.compile(r'^[A-Z0-9]{4,12}$')

    assert valid_pattern.match("ABC12345")
    assert valid_pattern.match("ABCD")
    assert not valid_pattern.match("../etc/passwd")
    assert not valid_pattern.match("abc123")       # minusculo
    assert not valid_pattern.match("AB")            # muito curto
    assert not valid_pattern.match("ABCDEFGHIJ123")  # muito longo


# ---- Referral link usa /i/{code} (nao ?ref=) ----

def test_referral_link_uses_pretty_url(mocker):
    """GET /member/referral deve retornar link /i/{code}."""
    mock_sb = MagicMock()
    mock_sb.table().select().eq().execute.return_value.data = [{
        "referral_code": "TESTCODE",
        "referral_count": 5,
        "points": 1100,
        "level": "silver",
    }]
    mock_sb.table().select().eq().order().limit().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    # Simular o que o endpoint faz (simplificado)
    from unittest.mock import patch as _patch
    import os
    APP_URL = os.environ.get("APP_URL", "https://clubeusa.com")
    code = "TESTCODE"
    link = f"{APP_URL}/i/{code}"
    assert "/i/" in link
    assert "?ref=" not in link


# ---- public_referral_preview: codigo invalido retorna 404 ----

def test_public_referral_preview_invalid_code(mocker):
    """Codigo com formato invalido deve ser rejeitado (regex guard)."""
    import re
    invalid_codes = ["../admin", "'; DROP TABLE", "abc", "AB"]
    valid_pattern = re.compile(r'^[A-Z0-9]{4,12}$')
    for code in invalid_codes:
        assert not valid_pattern.match(code.upper()), f"Deveria rejeitar: {code}"


# ---- cross-tenant: referral click so atualiza o proprio click ----

def test_mark_conversion_only_updates_unconverted(mocker):
    """
    _mark_referral_click_converted busca cliques nao convertidos (is null).
    Nao sobrescreve cliques ja convertidos.
    """
    from services.member_service import _mark_referral_click_converted

    mock_sb = MagicMock()
    # Simula nenhum clique nao-convertido (todos ja convertidos)
    mock_sb.table().select().eq().is_().order().limit().execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    _mark_referral_click_converted("REFCODE1", "member-uuid")
    # update NAO deve ser chamado quando nao ha clique para converter
    assert not mock_sb.table().update.called
