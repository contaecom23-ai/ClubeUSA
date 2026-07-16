"""Testes unitários para o módulo security — sem dependência de DB ou rede."""
import os

os.environ.setdefault("TESTING", "1")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-32chars!")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault("ENVIRONMENT", "development")

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from security import (
    create_access_token,
    decode_access_token,
    generate_token,
    hash_password,
    hash_token,
    verify_password,
)
from config import settings


class TestPasswordHashing:
    def test_hash_and_verify_correct(self):
        h = hash_password("minha_senha_123")
        assert verify_password("minha_senha_123", h)

    def test_verify_wrong_password(self):
        h = hash_password("correta")
        assert not verify_password("errada", h)

    def test_hashes_are_different_each_time(self):
        h1 = hash_password("mesmasenha")
        h2 = hash_password("mesmasenha")
        # bcrypt usa salt aleatório — hashes nunca são idênticos
        assert h1 != h2
        # mas ambos devem verificar a senha original
        assert verify_password("mesmasenha", h1)
        assert verify_password("mesmasenha", h2)

    def test_wrong_password_does_not_verify(self):
        h = hash_password("senha-correta")
        assert not verify_password("senha-errada", h)

    def test_invalid_hash_returns_false(self):
        assert not verify_password("qualquer", "hash-invalido-nao-e-bcrypt")


class TestGenerateToken:
    def test_tokens_are_unique(self):
        tokens = {generate_token() for _ in range(100)}
        assert len(tokens) == 100  # todos únicos

    def test_token_min_length(self):
        t = generate_token(32)
        assert len(t) >= 32

    def test_token_is_urlsafe(self):
        for _ in range(20):
            t = generate_token()
            assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for c in t)


class TestHashToken:
    def test_deterministic(self):
        t = generate_token()
        assert hash_token(t) == hash_token(t)

    def test_different_tokens_different_hashes(self):
        assert hash_token("abc") != hash_token("def")

    def test_hash_not_equal_to_original(self):
        t = generate_token()
        assert hash_token(t) != t


class TestJWT:
    def test_create_and_decode(self):
        token = create_access_token("user-uuid-123")
        user_id = decode_access_token(token)
        assert user_id == "user-uuid-123"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("nao.e.um.jwt.valido") is None

    def test_wrong_secret_returns_none(self):
        from jose import jwt as jose_jwt
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "type": "access",
        }
        bad_token = jose_jwt.encode(payload, "outra-chave-secreta", algorithm="HS256")
        assert decode_access_token(bad_token) is None

    def test_wrong_type_returns_none(self):
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "type": "refresh",  # tipo errado
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        assert decode_access_token(token) is None

    def test_expired_token_returns_none(self):
        payload = {
            "sub": "user-123",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        assert decode_access_token(token) is None

    def test_missing_sub_returns_none(self):
        payload = {
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
        assert decode_access_token(token) is None
