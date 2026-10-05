import asyncio
import hashlib
import pytest
from datetime import datetime, timezone, timedelta


# ---- Pure logic helpers ----

def test_hash_token_is_deterministic():
    from routers.email_confirmation import _hash_token
    assert _hash_token("abc") == _hash_token("abc")


def test_hash_token_matches_sha256():
    from routers.email_confirmation import _hash_token
    assert _hash_token("hello") == hashlib.sha256(b"hello").hexdigest()


def test_hash_token_different_inputs_differ():
    from routers.email_confirmation import _hash_token
    assert _hash_token("token_a") != _hash_token("token_b")


def test_page_sucesso_uses_green_color():
    from routers.email_confirmation import _page
    html = _page("sucesso", "Email confirmado!", "Tudo certo")
    assert "<!DOCTYPE html>" in html
    assert "Email confirmado!" in html
    assert "#22c55e" in html  # green for success


def test_page_erro_uses_red_color():
    from routers.email_confirmation import _page
    html = _page("erro", "Erro", "Algo deu errado")
    assert "#ef4444" in html  # red for error


def test_page_info_uses_blue_color():
    from routers.email_confirmation import _page
    html = _page("info", "Info", "Mensagem")
    assert "#3b82f6" in html  # blue for info


# ---- Router flow tests ----

class _Sb:
    """Chainable Supabase mock: any method chain ending in .execute() returns data."""
    def __init__(self, data):
        self._data = data

    def __call__(self, *a, **kw):
        return self

    def __getattr__(self, n):
        if n == "execute":
            data = self._data
            return lambda *a, **kw: type("R", (), {"data": data})()
        return self


def test_confirm_email_empty_token_returns_400():
    from routers.email_confirmation import confirm_email
    resp = asyncio.run(confirm_email(""))
    assert resp.status_code == 400


def test_confirm_email_too_long_token_returns_400():
    from routers.email_confirmation import confirm_email
    resp = asyncio.run(confirm_email("x" * 201))
    assert resp.status_code == 400


def test_confirm_email_token_not_in_db_returns_400(mocker):
    mocker.patch("routers.email_confirmation._supabase", return_value=_Sb([]))
    from routers.email_confirmation import confirm_email
    resp = asyncio.run(confirm_email("a" * 43))
    assert resp.status_code == 400


def test_confirm_email_already_used_returns_200(mocker):
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    rec = {"id": "t1", "member_id": "m1", "expires_at": future, "used_at": "2026-01-01T00:00:00Z"}
    mocker.patch("routers.email_confirmation._supabase", return_value=_Sb([rec]))
    from routers.email_confirmation import confirm_email
    resp = asyncio.run(confirm_email("a" * 43))
    assert resp.status_code == 200


def test_confirm_email_expired_token_returns_400(mocker):
    past = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    rec = {"id": "t1", "member_id": "m1", "expires_at": past, "used_at": None}
    mocker.patch("routers.email_confirmation._supabase", return_value=_Sb([rec]))
    from routers.email_confirmation import confirm_email
    resp = asyncio.run(confirm_email("a" * 43))
    assert resp.status_code == 400
