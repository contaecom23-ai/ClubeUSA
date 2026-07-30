"""Unit tests para o módulo security.py — sem I/O."""
import pytest

# conftest.py já define as env vars antes deste import
from security import (
    create_access_token,
    decode_access_token,
    generate_email_token,
    hash_password,
    verify_password,
)


def test_password_hash_and_verify():
    plain = "Senh@Forte123"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)


def test_password_wrong_returns_false():
    hashed = hash_password("senha-correta")
    assert not verify_password("senha-errada", hashed)


def test_jwt_roundtrip():
    uid = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(uid)
    assert decode_access_token(token) == uid


def test_jwt_tampered_returns_none():
    token = create_access_token("some-user-id") + "tampered"
    assert decode_access_token(token) is None


def test_jwt_garbage_returns_none():
    assert decode_access_token("not.a.jwt") is None


def test_generate_email_token_unique():
    t1 = generate_email_token()
    t2 = generate_email_token()
    assert t1 != t2
    assert len(t1) >= 32
