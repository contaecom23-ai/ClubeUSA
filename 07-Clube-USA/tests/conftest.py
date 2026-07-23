"""
Test configuration for Clube USA backend.

Tests use FastAPI's TestClient with a mocked DB pool (no real PostgreSQL required).
Rate limiting is disabled so tests can call endpoints freely.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.pw_utils import hash_password
from app.jwt_utils import make_access_token


# ── In-memory fake database ───────────────────────────────────────────────────

class FakeDB:
    def __init__(self):
        self.users: dict[str, dict] = {}
        self.profiles: dict[str, dict] = {}

    def reset(self):
        self.users.clear()
        self.profiles.clear()

    def find_by_email(self, email: str) -> dict | None:
        return next((u for u in self.users.values() if u["email"] == email), None)

    def find_by_token(self, token: str) -> dict | None:
        return next((u for u in self.users.values() if u.get("email_confirm_token") == token), None)

    def find_by_id(self, uid: str) -> dict | None:
        return self.users.get(str(uid))

    def find_by_referral(self, code: str) -> dict | None:
        return next((u for u in self.users.values() if u.get("referral_code") == code), None)


_db = FakeDB()


class FakeRecord(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


def row(data: dict) -> FakeRecord:
    return FakeRecord(data)


# ── Fake asyncpg connection ───────────────────────────────────────────────────

class FakeConn:
    async def fetchrow(self, query: str, *args):
        q = query.strip().upper()

        # Referral lookup: SELECT id FROM users WHERE referral_code = $1
        if "REFERRAL_CODE = $1" in q and "SELECT ID" in q:
            u = _db.find_by_referral(args[0])
            return row({"id": u["id"]}) if u else None

        # Duplicate check: SELECT 1 FROM users WHERE email = $1
        if "SELECT 1 FROM USERS WHERE EMAIL" in q:
            return row({"1": 1}) if _db.find_by_email(args[0]) else None

        # Register INSERT
        if "INSERT INTO USERS" in q:
            uid = str(uuid.uuid4())
            user = {
                "id": uid,
                "email": args[0],
                "password_hash": args[1],
                "full_name": args[2],
                "email_confirm_token": args[3],
                "email_confirm_expires_at": args[4],
                "referred_by_user_id": args[5],
                "email_confirmed": False,
                "referral_code": uid[:8],
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
            _db.users[uid] = user
            _db.profiles[uid] = {
                "user_id": uid, "us_state": None, "us_city": None,
                "whatsapp": None, "bio": None, "avatar_url": None,
                "updated_at": datetime.now(timezone.utc),
            }
            return row(user)

        # Confirm-email lookup: WHERE email_confirm_token = $1
        if "EMAIL_CONFIRM_TOKEN = $1" in q:
            u = _db.find_by_token(args[0])
            return row(u) if u else None

        # Auth deps + login: WHERE id = $1 AND IS_ACTIVE
        if "WHERE ID = $1 AND IS_ACTIVE" in q:
            u = _db.find_by_id(str(args[0]))
            return row(u) if (u and u.get("is_active")) else None

        # Login: WHERE email = $1 AND IS_ACTIVE
        if "WHERE EMAIL = $1 AND IS_ACTIVE" in q:
            u = _db.find_by_email(args[0])
            return row(u) if (u and u.get("is_active")) else None

        # Profile select
        if "FROM PROFILES WHERE USER_ID = $1" in q:
            p = _db.profiles.get(str(args[0]))
            return row(p) if p else None

        # Users select by id (profile update return)
        if "FROM USERS WHERE ID = $1" in q:
            u = _db.find_by_id(str(args[0]))
            return row(u) if u else None

        return None

    async def fetchval(self, query: str, *args):
        q = query.strip().upper()

        if "SELECT 1 FROM USERS WHERE EMAIL" in q:
            return 1 if _db.find_by_email(args[0]) else None

        if "COUNT(*) FROM USERS WHERE REFERRED_BY_USER_ID" in q:
            uid = str(args[0])
            if "AND EMAIL_CONFIRMED" in q:
                return sum(1 for u in _db.users.values()
                           if str(u.get("referred_by_user_id", "")) == uid and u.get("email_confirmed"))
            return sum(1 for u in _db.users.values()
                       if str(u.get("referred_by_user_id", "")) == uid)
        return None

    async def execute(self, query: str, *args):
        q = query.strip().upper()

        # Confirm email: UPDATE users SET email_confirmed = TRUE ... WHERE id = $1
        if "SET EMAIL_CONFIRMED = TRUE" in q:
            uid = str(args[0])
            u = _db.find_by_id(uid)
            if u:
                u["email_confirmed"] = True
                u["email_confirm_token"] = None
                u["email_confirm_expires_at"] = None
            return

        # UPDATE users SET full_name = $1 WHERE id = $2
        if "SET FULL_NAME" in q:
            u = _db.find_by_id(str(args[1]))
            if u:
                u["full_name"] = args[0]
            return

        # UPDATE profiles ...
        if "UPDATE PROFILES SET" in q:
            return


@asynccontextmanager
async def fake_get_conn():
    yield FakeConn()


# ── pytest fixtures ────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_db():
    _db.reset()


@pytest.fixture
def client():
    os.environ.setdefault("DATABASE_URL", "postgresql://fake/fake")
    os.environ.setdefault("SECRET_KEY", "test-secret-key-32-bytes-minimum!x")
    os.environ.setdefault("ENV", "test")

    # Patch DB connection and email; disable rate limiting for tests
    with patch("app.db.init_pool", new=AsyncMock()), \
         patch("app.db.get_conn", new=fake_get_conn), \
         patch("app.email_service.send_confirmation_email", new=AsyncMock()), \
         patch("app.limiter.limiter.enabled", new=False, create=True):
        from main import app
        # Disable rate limiter on the live app instance
        app.state.limiter._enabled = False  # type: ignore[attr-defined]
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c


@pytest.fixture
def registered_user() -> dict:
    """Insert a test user directly into the fake DB (bypasses rate limiting)."""
    uid = str(uuid.uuid4())
    token = "confirm-token-abc123"
    user = {
        "id": uid,
        "email": "test@example.com",
        "password_hash": hash_password("securePass1"),
        "full_name": "Test User",
        "email_confirm_token": token,
        "email_confirm_expires_at": datetime.now(timezone.utc) + timedelta(hours=24),
        "referred_by_user_id": None,
        "email_confirmed": False,
        "referral_code": "testcode",
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }
    _db.users[uid] = user
    _db.profiles[uid] = {
        "user_id": uid, "us_state": None, "us_city": None,
        "whatsapp": None, "bio": None, "avatar_url": None,
        "updated_at": datetime.now(timezone.utc),
    }
    return user


@pytest.fixture
def confirmed_user_token(client, registered_user) -> str:
    """Confirm email via the API and return a valid JWT."""
    token = registered_user["email_confirm_token"]
    res = client.get(f"/auth/confirm-email?token={token}")
    assert res.status_code == 200, f"Confirm failed: {res.json()}"
    return res.json()["access_token"]
