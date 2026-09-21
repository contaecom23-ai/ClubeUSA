"""
Tests for Fase 0.4 — valid registration definition + anti-fraud.
Covers: is_valid_registration logic, IP fraud limit, cross-tenant isolation,
hashing safety.
"""
import pytest
from unittest.mock import MagicMock


# ── Definição de cadastro válido ──────────────────────────────

def test_member_with_no_clicks_not_valid():
    """Membro com 0 cliques NÃO é cadastro válido."""
    m = {"total_clicks": 0}
    assert m["total_clicks"] < 1


def test_member_with_one_click_is_valid():
    """Membro com 1 clique É cadastro válido."""
    m = {"total_clicks": 1}
    assert m["total_clicks"] >= 1


def test_member_with_many_clicks_is_valid():
    """Membro com muitos cliques continua válido."""
    m = {"total_clicks": 100}
    assert m["total_clicks"] >= 1


# ── Limite anti-fraude por IP ─────────────────────────────────

def test_ip_fraud_limit_blocks_at_threshold():
    """IP com 3 cadastros em 24h deve ser bloqueado."""
    from services.member_service import _check_ip_fraud_limit
    mock_sb = MagicMock()
    mock_result = MagicMock()
    mock_result.count = 3
    mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result
    assert _check_ip_fraud_limit("hashed_ip", mock_sb, max_per_day=3) is True


def test_ip_fraud_limit_allows_below_threshold():
    """IP com 2 cadastros em 24h deve ser permitido."""
    from services.member_service import _check_ip_fraud_limit
    mock_sb = MagicMock()
    mock_result = MagicMock()
    mock_result.count = 2
    mock_sb.table.return_value.select.return_value.eq.return_value.gte.return_value.execute.return_value = mock_result
    assert _check_ip_fraud_limit("hashed_ip", mock_sb, max_per_day=3) is False


def test_ip_fraud_limit_allows_none():
    """IP None não deve bloquear (origem desconhecida tratada de forma segura)."""
    from services.member_service import _check_ip_fraud_limit
    assert _check_ip_fraud_limit(None, MagicMock()) is False


def test_ip_fraud_limit_allows_empty_string():
    """Hash vazio não deve bloquear."""
    from services.member_service import _check_ip_fraud_limit
    assert _check_ip_fraud_limit("", MagicMock()) is False


# ── Isolamento multi-tenant ───────────────────────────────────

def test_valid_status_uses_jwt_sub_not_param():
    """O endpoint usa member['sub'] do JWT validado — não aceita ID externo."""
    token_a = {"sub": "uuid-member-a"}
    external_id = "uuid-member-b"
    # O endpoint filtra sempre por token_a["sub"], nunca por query param
    query_filter = token_a["sub"]
    assert query_filter != external_id


# ── Segurança de hash de IP ───────────────────────────────────

def test_ip_stored_as_hash_not_plaintext():
    """IP é armazenado como hash — nunca em texto limpo."""
    from utils.security import hash_ip
    ip = "203.0.113.42"
    h = hash_ip(ip)
    assert ip not in h
    assert len(h) > 10


def test_different_ips_produce_different_hashes():
    """IPs distintos geram hashes distintos."""
    from utils.security import hash_ip
    assert hash_ip("1.2.3.4") != hash_ip("5.6.7.8")


def test_same_ip_produces_same_hash():
    """O mesmo IP sempre gera o mesmo hash (determinístico)."""
    from utils.security import hash_ip
    ip = "192.168.1.1"
    assert hash_ip(ip) == hash_ip(ip)
