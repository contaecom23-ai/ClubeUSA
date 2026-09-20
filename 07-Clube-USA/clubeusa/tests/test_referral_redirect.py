# tests/test_referral_redirect.py — Clube USA
# Testa a lógica da rota GET /i/{code} (pretty URL de indicação)
#
# Testa a função diretamente via app mínimo (evita importar o main.py
# completo com todas as dependências pesadas).

import re
import pytest
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.testclient import TestClient


# ── App mínimo que replica a lógica da rota /i/{code} ────────

_app = FastAPI()


@_app.get("/i/{code}", include_in_schema=False)
async def referral_redirect(code: str):
    normalized = code.upper()
    if re.match(r'^[A-Z0-9]{4,12}$', normalized):
        return RedirectResponse(url=f"/?ref={normalized}", status_code=302)
    return RedirectResponse(url="/", status_code=302)


client = TestClient(_app, follow_redirects=False)


# ── Testes ────────────────────────────────────────────────────

def test_valid_8char_code_redirects_with_ref():
    """Código de 8 chars (formato padrão) → 302 para /?ref=CODE."""
    resp = client.get("/i/XK7M3NP2")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=XK7M3NP2"


def test_code_normalized_to_uppercase():
    """Código em minúsculas é normalizado para maiúsculas."""
    resp = client.get("/i/abc12345")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12345"


def test_mixed_case_normalized():
    resp = client.get("/i/AbC12xYz")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/?ref=ABC12XYZ"


def test_short_code_4chars_valid():
    """Mínimo de 4 chars → redireciona com ref."""
    resp = client.get("/i/ABCD")
    assert resp.status_code == 302
    assert "ref=ABCD" in resp.headers["location"]


def test_long_code_12chars_valid():
    """Máximo de 12 chars → redireciona com ref."""
    resp = client.get("/i/ABCDEFGH1234")
    assert resp.status_code == 302
    assert "ref=ABCDEFGH1234" in resp.headers["location"]


def test_too_short_redirects_to_root():
    """Menos de 4 chars → 302 para / sem ref."""
    resp = client.get("/i/AB")
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"
    assert "ref=" not in resp.headers["location"]


def test_too_long_redirects_to_root():
    """Mais de 12 chars → 302 para / sem ref."""
    resp = client.get("/i/ABCDEFGH12345")  # 13 chars
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"
    assert "ref=" not in resp.headers["location"]


def test_code_with_hyphen_redirects_to_root():
    """Código com hífen (inválido) → 302 para / sem ref."""
    resp = client.get("/i/ABC-1234")
    assert resp.status_code == 302
    assert "ref=" not in resp.headers["location"]


def test_code_with_space_encoded_redirects_to_root():
    """Espaço codificado no código → 302 para / sem ref (XSS guard)."""
    resp = client.get("/i/ABC%2012")
    assert resp.status_code == 302
    assert "ref=" not in resp.headers["location"]
