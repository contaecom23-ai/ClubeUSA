"""Tests for Fase 0.1 auth flows."""
import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-key")
os.environ.setdefault("JWT_SECRET", "test-jwt-secret-that-is-long-enough-ok")

from app.auth.utils import (
    create_access_token,
    decode_access_token,
    generate_opaque_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.auth.service import register_user, verify_email, login_user


# ── Utils ─────────────────────────────────────────────────────────────────────

def test_password_hash_and_verify():
    pw = "SecurePass123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed)
    assert not verify_password("wrongpassword1", hashed)


def test_opaque_token_is_unique():
    t1 = generate_opaque_token()
    t2 = generate_opaque_token()
    assert t1 != t2
    assert len(t1) >= 40


def test_hash_token_deterministic():
    token = generate_opaque_token()
    assert hash_token(token) == hash_token(token)
    assert hash_token("a") != hash_token("b")


def test_jwt_roundtrip():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token, expires_in = create_access_token(user_id)
    assert expires_in > 0
    decoded = decode_access_token(token)
    assert decoded == user_id


def test_jwt_tampered_raises():
    from jose import JWTError
    user_id = "some-user-id"
    token, _ = create_access_token(user_id)
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(Exception):
        decode_access_token(tampered)


# ── Registration service ──────────────────────────────────────────────────────

def _make_db_for_register(existing_users=None):
    """Returns a fake DB client suitable for register_user()."""
    from tests.conftest import FakeQueryBuilder
    db = MagicMock()

    call_count = {"n": 0}

    def table_side_effect(table_name):
        qb = MagicMock()
        qb.select.return_value = qb
        qb.insert.return_value = qb
        qb.update.return_value = qb
        qb.eq.return_value = qb

        def execute_side():
            result = MagicMock()
            if table_name == "users" and call_count["n"] == 0:
                # First call = duplicate check
                result.data = existing_users or []
                call_count["n"] += 1
            elif table_name == "users":
                # Second call = insert
                result.data = [{
                    "id": "new-user-id",
                    "email": "test@example.com",
                    "name": "Test User",
                }]
            else:
                result.data = []
            return result

        qb.execute.side_effect = execute_side
        return qb

    db.table.side_effect = table_side_effect
    return db


def test_register_success():
    db = _make_db_for_register()
    with patch("app.auth.service.send_verification_email"):
        user = register_user(db, email="test@example.com", password="Password123", name="Test User", zip_code=None, state_abbr=None)
    assert user["email"] == "test@example.com"


def test_register_duplicate_email():
    from fastapi import HTTPException
    db = _make_db_for_register(existing_users=[{"id": "existing-id"}])
    with pytest.raises(HTTPException) as exc_info:
        register_user(db, email="dupe@example.com", password="Password123", name="Test User", zip_code=None, state_abbr=None)
    assert exc_info.value.status_code == 409


# ── Email verification service ────────────────────────────────────────────────

def test_verify_email_invalid_token():
    from fastapi import HTTPException
    from datetime import datetime, timezone

    db = MagicMock()
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    result = MagicMock()
    result.data = []
    qb.execute.return_value = result
    db.table.return_value = qb

    with pytest.raises(HTTPException) as exc_info:
        verify_email(db, token="invalidtoken123456789012345678901234")
    assert exc_info.value.status_code == 400


def test_verify_email_already_verified():
    from datetime import datetime, timezone

    token = generate_opaque_token()
    token_hash = hash_token(token)

    db = MagicMock()
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    result = MagicMock()
    result.data = [{
        "id": "user-id",
        "email_verified": True,
        "email_verification_sent_at": datetime.now(tz=timezone.utc).isoformat(),
    }]
    qb.execute.return_value = result
    db.table.return_value = qb

    # Should not raise — idempotent
    verify_email(db, token=token)


# ── Login service ─────────────────────────────────────────────────────────────

def test_login_wrong_password():
    from fastapi import HTTPException

    real_hash = hash_password("CorrectPassword1")
    db = MagicMock()
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    result = MagicMock()
    result.data = [{"id": "uid", "password_hash": real_hash, "name": "User", "email_verified": True}]
    qb.execute.return_value = result
    db.table.return_value = qb

    with pytest.raises(HTTPException) as exc_info:
        login_user(db, email="u@example.com", password="WrongPassword1")
    assert exc_info.value.status_code == 401


def test_login_email_not_verified():
    from fastapi import HTTPException

    real_hash = hash_password("Password123")
    db = MagicMock()
    qb = MagicMock()
    qb.select.return_value = qb
    qb.eq.return_value = qb
    result = MagicMock()
    result.data = [{"id": "uid", "password_hash": real_hash, "name": "User", "email_verified": False}]
    qb.execute.return_value = result
    db.table.return_value = qb

    with pytest.raises(HTTPException) as exc_info:
        login_user(db, email="u@example.com", password="Password123")
    assert exc_info.value.status_code == 403


def test_login_success():
    real_hash = hash_password("Password123")
    insert_qb = MagicMock()
    insert_qb.insert.return_value = insert_qb
    insert_result = MagicMock()
    insert_result.data = [{"id": "rt-id"}]
    insert_qb.execute.return_value = insert_result

    select_qb = MagicMock()
    select_qb.select.return_value = select_qb
    select_qb.eq.return_value = select_qb
    select_result = MagicMock()
    select_result.data = [{"id": "uid", "password_hash": real_hash, "name": "User", "email_verified": True}]
    select_qb.execute.return_value = select_result

    def table_side(name):
        if name == "refresh_tokens":
            return insert_qb
        return select_qb

    db = MagicMock()
    db.table.side_effect = table_side

    tokens = login_user(db, email="u@example.com", password="Password123")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"
