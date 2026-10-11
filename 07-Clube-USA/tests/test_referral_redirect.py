# tests/test_referral_redirect.py — Clube USA
# Testes para resolve_referral_code e a rota GET /i/{code} (Fase 0.2).

import pytest
from unittest.mock import MagicMock


# ============================================================
#  resolve_referral_code (member_service)
# ============================================================

def test_resolve_valid_code(mocker):
    """Código válido e ativo → retorna member_id."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "member-1"}
    ]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resolve_referral_code
    member_id = resolve_referral_code("JOAO12")

    assert member_id == "member-1"


def test_resolve_normalizes_lowercase(mocker):
    """Código em minúsculas é normalizado antes da consulta."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"id": "member-1"}
    ]
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resolve_referral_code
    member_id = resolve_referral_code("joao12")

    assert member_id == "member-1"
    # Verifica que a consulta foi feita com o código em maiúsculas
    first_eq_call = mock_sb.table.return_value.select.return_value.eq.call_args_list[0]
    assert first_eq_call.args == ("referral_code", "JOAO12")


def test_resolve_code_not_found(mocker):
    """Código inexistente → ValueError."""
    mock_sb = MagicMock()
    mock_sb.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = []
    mocker.patch("services.member_service._supabase", return_value=mock_sb)

    from services.member_service import resolve_referral_code
    with pytest.raises(ValueError, match="[Nn]ão encontrado|[Nn]ao encontrado"):
        resolve_referral_code("NAOEXISTE")


def test_resolve_code_too_short():
    """Código com menos de 4 caracteres → ValueError sem consultar o banco."""
    from services.member_service import resolve_referral_code
    with pytest.raises(ValueError, match="[Ff]ormato|[Ii]nv"):
        resolve_referral_code("AB")


def test_resolve_code_too_long():
    """Código com mais de 12 caracteres → ValueError."""
    from services.member_service import resolve_referral_code
    with pytest.raises(ValueError, match="[Ff]ormato|[Ii]nv"):
        resolve_referral_code("ABCDEF1234567")


def test_resolve_code_with_special_chars():
    """Código com caracteres especiais → ValueError."""
    from services.member_service import resolve_referral_code
    with pytest.raises(ValueError, match="[Ff]ormato|[Ii]nv"):
        resolve_referral_code("JO@O12")


def test_resolve_empty_code():
    """Código vazio → ValueError."""
    from services.member_service import resolve_referral_code
    with pytest.raises(ValueError, match="[Aa]usente|[Ee]mpty|[Ii]nv"):
        resolve_referral_code("")
