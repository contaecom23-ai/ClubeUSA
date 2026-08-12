import os
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from jose import jwt

# Env vars devem estar definidas antes de importar o app
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
os.environ.setdefault(
    "SUPABASE_JWT_SECRET",
    "test-jwt-secret-that-is-long-enough-for-hs256-algorithm",
)
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:3000")

from app import dependencies  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.main import app  # noqa: E402

TEST_JWT_SECRET = os.environ["SUPABASE_JWT_SECRET"]
TEST_USER_ID = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
TEST_OTHER_USER_ID = "ffffffff-eeee-dddd-cccc-bbbbbbbbbbbb"
TEST_EMAIL = "joao@example.com"


def make_token(
    user_id: str = TEST_USER_ID,
    email: str = TEST_EMAIL,
    expired: bool = False,
) -> str:
    exp = datetime.now(tz=timezone.utc) + (
        timedelta(seconds=-10) if expired else timedelta(hours=1)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": exp,
        "iat": datetime.now(tz=timezone.utc),
    }
    return jwt.encode(payload, TEST_JWT_SECRET, algorithm="HS256")


def _make_mock_supabase(
    register_raises=None,
    login_raises=None,
    login_session=None,
    profile_data=None,
    update_data=None,
    refresh_raises=None,
    refresh_session=None,
) -> MagicMock:
    mock = MagicMock()

    if register_raises:
        mock.auth.sign_up.side_effect = register_raises
    else:
        mock.auth.sign_up.return_value = MagicMock(user=MagicMock(id=TEST_USER_ID), session=None)

    if login_raises:
        mock.auth.sign_in_with_password.side_effect = login_raises
    else:
        session = login_session or MagicMock(
            access_token="access-token-xyz",
            refresh_token="refresh-token-xyz",
            expires_in=3600,
        )
        mock.auth.sign_in_with_password.return_value = MagicMock(session=session)

    if refresh_raises:
        mock.auth.refresh_session.side_effect = refresh_raises
    else:
        rs = refresh_session or MagicMock(
            access_token="new-access-token",
            refresh_token="new-refresh-token",
            expires_in=3600,
        )
        mock.auth.refresh_session.return_value = MagicMock(session=rs)

    # DB table mock
    _profile = profile_data or {
        "id": TEST_USER_ID,
        "first_name": "João",
        "last_name": "Silva",
        "zip_code": "10001",
        "phone": None,
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }

    table_mock = MagicMock()
    select_chain = MagicMock()
    select_chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=_profile
    )

    _updated = update_data or {**_profile, "first_name": "João Updated"}
    update_chain = MagicMock()
    update_chain.eq.return_value.execute.return_value = MagicMock(data=[_updated])

    table_mock.select.return_value = select_chain
    table_mock.update.return_value = update_chain
    mock.table.return_value = table_mock

    return mock


@pytest.fixture()
def mock_supabase() -> MagicMock:
    return _make_mock_supabase()


@pytest.fixture()
def client(mock_supabase: MagicMock) -> TestClient:
    get_settings.cache_clear()
    original = dependencies._supabase_client
    dependencies._supabase_client = mock_supabase
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    dependencies._supabase_client = original


@pytest.fixture()
def auth_headers() -> dict:
    return {"Authorization": f"Bearer {make_token()}"}
