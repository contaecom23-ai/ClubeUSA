"""Unit tests for security helpers — no DB or network required."""
import pytest

# conftest.py sets env vars before this import
from security import (
    create_access_token,
    decode_access_token,
    generate_confirmation_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password():
    hashed = hash_password("correctPassword123")
    assert verify_password("correctPassword123", hashed)
    assert not verify_password("wrongPassword", hashed)


def test_different_passwords_produce_different_hashes():
    h1 = hash_password("password1")
    h2 = hash_password("password1")
    # bcrypt salts each hash differently
    assert h1 != h2
    assert verify_password("password1", h1)
    assert verify_password("password1", h2)


def test_jwt_roundtrip():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(user_id)
    assert isinstance(token, str)
    decoded = decode_access_token(token)
    assert decoded == user_id


def test_invalid_token_returns_none():
    assert decode_access_token("not-a-jwt") is None
    assert decode_access_token("") is None


def test_tampered_token_returns_none():
    token = create_access_token("some-user-id")
    # Flip a character in the signature
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert decode_access_token(tampered) is None


def test_confirmation_token_is_high_entropy():
    t1 = generate_confirmation_token()
    t2 = generate_confirmation_token()
    assert t1 != t2
    # token_urlsafe(32) produces ~43 URL-safe chars
    assert len(t1) >= 40
