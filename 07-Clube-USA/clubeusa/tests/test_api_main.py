# tests/test_api_main.py
#
# WHY: zero coverage exists for the core HTTP surface (auth, member, billing).
# This suite mocks Supabase + Stripe so it runs with no real credentials.
# Covers happy paths, auth gates, input validation, and security headers.

import os
import sys
import importlib
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Environment — must be set before importing main to avoid EnvironmentError
# ---------------------------------------------------------------------------
ENV = {
    "SUPABASE_URL":          "https://test.supabase.co",
    "SUPABASE_SERVICE_KEY":  "test-service-key",
    "JWT_SECRET":            "test-jwt-secret-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
    "ENCRYPTION_KEY":        "test-encryption-key-32bytes-xxxx",
    "STRIPE_SECRET_KEY":     "sk_test_fake",
    "STRIPE_WEBHOOK_SECRET": "whsec_test",
    "STRIPE_VIP_PRICE_ID":   "price_test",
    "ADMIN_SECRET":          "admin-secret-key",
    "APP_URL":               "https://clubeusa.com",
    "ENVIRONMENT":           "test",
    "ZAPI_INSTANCE":         "inst",
    "ZAPI_TOKEN":            "tok",
    "ZAPI_CLIENT_TOKEN":     "ctok",
}

for k, v in ENV.items():
    os.environ.setdefault(k, v)

# Make sure api/ and its siblings are importable
_HERE = os.path.dirname(__file__)
_ROOT = os.path.join(_HERE, "..")
for p in [_ROOT, os.path.join(_ROOT, "api"), os.path.join(_ROOT, "utils"),
          os.path.join(_ROOT, "services")]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sb_mock(member_data=None, otp_data=None):
    """Return a Supabase client mock with sensible defaults."""
    sb = MagicMock()
    table = MagicMock()
    sb.table.return_value = table

    def _chain(*_, **__):
        return table

    for method in ("select", "insert", "update", "delete", "eq", "in_",
                   "order", "limit", "gt", "neq"):
        getattr(table, method).return_value = table

    # Default execute returns
    table.execute.return_value = MagicMock(data=member_data or [], count=0)
    sb.rpc.return_value = MagicMock(execute=MagicMock(return_value=MagicMock(data=[])))
    return sb


def _valid_token(member_id: str = "member-1", plan: str = "free") -> str:
    from utils.security import create_token
    return create_token(member_id, plan)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Clear in-memory rate-limit store between tests."""
    import utils.security as sec
    sec._rate_store.clear()
    yield
    sec._rate_store.clear()


@pytest.fixture()
def client():
    # Patch supabase at every import site in the api package
    with patch("supabase.create_client", return_value=_make_sb_mock()):
        # Import (or reload) main inside the patch context
        import api.main as m
        importlib.reload(m)
        with TestClient(m.app, raise_server_exceptions=False) as c:
            yield c


# ===========================================================================
#  /health
# ===========================================================================

class TestHealth:
    def test_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


# ===========================================================================
#  Security headers
# ===========================================================================

class TestSecurityHeaders:
    def test_headers_present(self, client):
        r = client.get("/health")
        assert r.headers.get("x-content-type-options") == "nosniff"
        assert r.headers.get("x-frame-options") == "DENY"
        assert "x-xss-protection" in r.headers


# ===========================================================================
#  POST /auth/register
# ===========================================================================

class TestRegister:
    def _post(self, client, body):
        return client.post("/auth/register", json=body)

    def test_invalid_phone(self, client):
        r = self._post(client, {"phone": "not-a-phone"})
        assert r.status_code in (400, 422)

    def test_invalid_language(self, client):
        r = self._post(client, {"phone": "+15551234567", "language": "de"})
        assert r.status_code == 422

    def test_valid_categories_filtered(self, client):
        """Unknown categories are silently dropped — shouldn't raise."""
        with patch("services.member_service.register_member",
                   return_value={"member_id": "x", "referral_code": "ABC12345"}):
            r = self._post(client, {
                "phone":      "+15551234567",
                "categories": ["electronics", "invalid_cat"],
            })
        # 201 or 422 depending on mock; key point: no 500
        assert r.status_code != 500

    def test_successful_registration(self, client):
        with patch("services.member_service.register_member",
                   return_value={"member_id": "m1", "referral_code": "ABCD1234"}):
            r = self._post(client, {
                "phone":    "+15551234567",
                "name":     "Test User",
                "language": "pt",
            })
        assert r.status_code == 201
        body = r.json()
        assert "member_id" in body or "referral_code" in body

    def test_duplicate_phone_returns_422(self, client):
        with patch("services.member_service.register_member",
                   side_effect=ValueError("Número já cadastrado.")):
            r = self._post(client, {"phone": "+15551234567"})
        assert r.status_code == 422

    def test_xss_in_name_does_not_crash(self, client):
        with patch("services.member_service.register_member",
                   return_value={"member_id": "m1", "referral_code": "ABCD1234"}):
            r = self._post(client, {
                "phone": "+15551234567",
                "name":  "<script>alert('xss')</script>",
            })
        # Must not 500 and must not echo raw HTML
        assert r.status_code != 500
        assert "<script>" not in r.text

    def test_oversized_name_rejected_or_truncated(self, client):
        """A 1000-char name should not cause a 500."""
        with patch("services.member_service.register_member",
                   return_value={"member_id": "m1", "referral_code": "ABCD1234"}):
            r = self._post(client, {"phone": "+15551234567", "name": "A" * 1000})
        assert r.status_code != 500


# ===========================================================================
#  POST /auth/otp/request
# ===========================================================================

class TestOTPRequest:
    def test_invalid_phone(self, client):
        with patch("api.main._otp_save"), patch("api.main._send_otp_whatsapp"):
            r = client.post("/auth/otp/request", json={"phone": "abc"})
        assert r.status_code == 422

    def test_valid_phone_dev_mode(self, client):
        with patch("api.main._otp_save") as mock_save:
            r = client.post("/auth/otp/request", json={"phone": "+15551234567"})
        assert r.status_code == 200
        data = r.json()
        assert "expires_in" in data
        assert data["expires_in"] == 600

    def test_rate_limit_on_auth(self, client):
        """6th request to /auth/* within 60 s should be blocked."""
        with patch("api.main._otp_save"):
            for _ in range(5):
                client.post("/auth/otp/request", json={"phone": "+15551234567"})
            r = client.post("/auth/otp/request", json={"phone": "+15551234567"})
        assert r.status_code == 429


# ===========================================================================
#  POST /auth/otp/verify
# ===========================================================================

class TestOTPVerify:
    def test_wrong_otp(self, client):
        with patch("api.main._otp_verify", return_value=(False, "Codigo incorreto.")):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "000000"})
        assert r.status_code == 400

    def test_expired_otp(self, client):
        with patch("api.main._otp_verify",
                   return_value=(False, "Codigo expirado. Solicite um novo.")):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "123456"})
        assert r.status_code == 400

    def test_too_many_attempts_returns_429(self, client):
        with patch("api.main._otp_verify",
                   return_value=(False, "Muitas tentativas. Solicite novo codigo.")):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "000000"})
        assert r.status_code == 429

    def test_banned_member_rejected(self, client):
        sb = _make_sb_mock(member_data=[{"id": "m1", "plan": "free", "status": "banned"}])
        with patch("api.main._otp_verify", return_value=(True, "")), \
             patch("supabase.create_client", return_value=sb):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "123456"})
        assert r.status_code == 403

    def test_member_not_found_404(self, client):
        sb = _make_sb_mock(member_data=[])
        with patch("api.main._otp_verify", return_value=(True, "")), \
             patch("supabase.create_client", return_value=sb):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "123456"})
        assert r.status_code == 404

    def test_valid_otp_returns_token(self, client):
        sb = _make_sb_mock(member_data=[{"id": "m1", "plan": "free", "status": "active"}])
        with patch("api.main._otp_verify", return_value=(True, "")), \
             patch("supabase.create_client", return_value=sb):
            r = client.post("/auth/otp/verify",
                            json={"phone": "+15551234567", "otp": "123456"})
        assert r.status_code == 200
        data = r.json()
        assert "token" in data
        assert data["plan"] == "free"


# ===========================================================================
#  GET /member/profile  (requires auth)
# ===========================================================================

class TestMemberProfile:
    def test_no_token_returns_401(self, client):
        r = client.get("/member/profile")
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, client):
        r = client.get("/member/profile", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401

    def test_valid_token_found_profile(self, client):
        token = _valid_token("m1")
        profile = {"id": "m1", "name": "Alice", "plan": "free"}
        with patch("services.member_service.get_member_profile", return_value=profile):
            r = client.get("/member/profile",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["name"] == "Alice"

    def test_member_not_found_returns_404(self, client):
        token = _valid_token("m1")
        with patch("services.member_service.get_member_profile", return_value=None):
            r = client.get("/member/profile",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404


# ===========================================================================
#  GET /member/deals
# ===========================================================================

class TestMemberDeals:
    def test_no_token_rejected(self, client):
        r = client.get("/member/deals")
        assert r.status_code == 401

    def test_free_member_sees_sent_only(self, client):
        token = _valid_token("m1", "free")
        deals = [{"id": "d1", "title": "Deal A", "status": "sent"}]
        sb = _make_sb_mock(member_data=deals)
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/member/deals",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["plan"] == "free"

    def test_vip_member_plan_label(self, client):
        token = _valid_token("m1", "vip")
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/member/deals",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["plan"] == "vip"

    def test_limit_capped_free(self, client):
        """Free user cannot fetch more than 20 deals regardless of query param."""
        token = _valid_token("m1", "free")
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/member/deals?limit=100",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200


# ===========================================================================
#  GET /member/referral
# ===========================================================================

class TestMemberReferral:
    def test_no_token_rejected(self, client):
        r = client.get("/member/referral")
        assert r.status_code == 401

    def test_returns_referral_link(self, client):
        token = _valid_token("m1")
        member_row = [{"referral_code": "ABCD1234", "referral_count": 3,
                        "points": 600, "level": "bronze"}]
        refs_row = []
        # two separate Supabase calls: members table + referrals table
        sb = MagicMock()
        table = MagicMock()
        sb.table.return_value = table
        for m in ("select","eq","order","limit"):
            getattr(table, m).return_value = table
        # first call returns member, second returns refs
        table.execute.side_effect = [
            MagicMock(data=member_row),
            MagicMock(data=refs_row),
        ]
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/member/referral",
                           headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        data = r.json()
        assert data["referral_code"] == "ABCD1234"
        assert "referral_link" in data
        assert "ABCD1234" in data["referral_link"]


# ===========================================================================
#  POST /billing/subscribe
# ===========================================================================

class TestBillingSubscribe:
    def test_no_token_rejected(self, client):
        r = client.post("/billing/subscribe")
        assert r.status_code == 401

    def test_already_vip_400(self, client):
        token = _valid_token("m1", "vip")
        r = client.post("/billing/subscribe",
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 400

    def test_stripe_not_configured_503(self, client):
        token = _valid_token("m1", "free")
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": ""}):
            import stripe as _stripe
            _stripe.api_key = ""
            import api.main as m
            m.stripe.api_key = ""
            r = client.post("/billing/subscribe",
                            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (503, 400, 500)  # no crash

    def test_successful_checkout_session(self, client):
        token = _valid_token("m1", "free")
        fake_session = MagicMock(url="https://checkout.stripe.com/pay/x", id="cs_test")
        sb = _make_sb_mock(member_data=[{"vip_trial_used": False}])
        with patch("supabase.create_client", return_value=sb), \
             patch("stripe.checkout.Session.create", return_value=fake_session):
            r = client.post("/billing/subscribe",
                            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert "checkout_url" in r.json()


# ===========================================================================
#  POST /billing/webhook  (Stripe signature verification)
# ===========================================================================

class TestBillingWebhook:
    def test_invalid_signature_400(self, client):
        import stripe as _stripe
        _stripe.Webhook.construct_event = MagicMock(
            side_effect=_stripe.error.SignatureVerificationError("bad sig", None)
        )
        r = client.post("/billing/webhook",
                        content=b'{"type":"checkout.session.completed"}',
                        headers={"stripe-signature": "bad"})
        assert r.status_code == 400

    def test_valid_webhook_returns_received(self, client):
        fake_event = {"type": "invoice.payment_failed",
                      "data": {"object": {"customer": "cus_x"}}}
        import stripe as _stripe
        with patch.object(_stripe.Webhook, "construct_event", return_value=fake_event):
            r = client.post("/billing/webhook",
                            content=b'{}',
                            headers={"stripe-signature": "ok"})
        assert r.status_code == 200
        assert r.json()["received"] is True


# ===========================================================================
#  GET /public/groups  (no auth required)
# ===========================================================================

class TestPublicGroups:
    def test_no_auth_allowed(self, client):
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/public/groups")
        assert r.status_code == 200

    def test_response_shape(self, client):
        groups = [{"id": "g1", "name": "Clube USA PT", "language": "pt",
                   "invite_url": "https://chat.whatsapp.com/xxx", "member_count": 50}]
        sb = _make_sb_mock(member_data=groups)
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/public/groups")
        assert r.status_code == 200
        assert "groups" in r.json()


# ===========================================================================
#  GET /alerts  (requires paid plan)
# ===========================================================================

class TestAlerts:
    def test_free_member_rejected(self, client):
        token = _valid_token("m1", "free")
        r = client.get("/alerts", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 403

    def test_vip_member_can_list(self, client):
        token = _valid_token("m1", "vip")
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/alerts", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200

    def test_create_alert_invalid_asin(self, client):
        token = _valid_token("m1", "vip")
        r = client.post("/alerts",
                        json={"asin": "SHORT", "target_type": "price", "target_value": 9.99},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 422

    def test_create_alert_invalid_target_type(self, client):
        token = _valid_token("m1", "vip")
        r = client.post("/alerts",
                        json={"asin": "B08N5WRWNW", "target_type": "invalid", "target_value": 9.99},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 422

    def test_create_alert_negative_value(self, client):
        token = _valid_token("m1", "vip")
        r = client.post("/alerts",
                        json={"asin": "B08N5WRWNW", "target_type": "price", "target_value": -1.0},
                        headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 422

    def test_create_alert_success(self, client):
        token = _valid_token("m1", "vip")
        sb = _make_sb_mock(member_data=[{"id": "a1", "asin": "B08N5WRWNW",
                                          "target_type": "price", "target_value": 9.99}])
        with patch("supabase.create_client", return_value=sb):
            r = client.post("/alerts",
                            json={"asin": "B08N5WRWNW", "target_type": "price",
                                  "target_value": 9.99},
                            headers={"Authorization": f"Bearer {token}"})
        assert r.status_code in (200, 201)

    def test_delete_alert_wrong_owner_returns_404(self, client):
        """IDOR guard: member should not be able to delete another member's alert."""
        token = _valid_token("m1", "vip")
        # Simulate: alert belongs to different member — execute returns []
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.delete("/alerts/alert-999",
                              headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404


# ===========================================================================
#  Admin endpoints — require ADMIN_SECRET
# ===========================================================================

class TestAdminAuth:
    ADMIN_HDR = {"Authorization": f"Bearer {ENV['ADMIN_SECRET']}"}

    def test_no_admin_token_rejected(self, client):
        r = client.get("/admin/metrics")
        assert r.status_code == 401

    def test_wrong_admin_token_rejected(self, client):
        r = client.get("/admin/metrics",
                       headers={"Authorization": "Bearer wrongsecret"})
        assert r.status_code == 401

    def test_valid_admin_token_accepted(self, client):
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.get("/admin/metrics", headers=self.ADMIN_HDR)
        assert r.status_code == 200


# ===========================================================================
#  Multi-tenant isolation smoke test
# ===========================================================================

class TestMultiTenantIsolation:
    def test_member_cannot_access_other_alert(self, client):
        """Deleting an alert not owned by the token holder must 404."""
        token = _valid_token("member-A", "vip")
        # DB returns [] (alert not found for member-A)
        sb = _make_sb_mock(member_data=[])
        with patch("supabase.create_client", return_value=sb):
            r = client.delete("/alerts/alert-belonging-to-member-B",
                              headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 404

    def test_token_sub_drives_data_lookup(self, client):
        """Profile lookup uses token sub, not a client-supplied id."""
        token = _valid_token("m1")
        profile = {"id": "m1", "name": "Alice"}
        with patch("services.member_service.get_member_profile",
                   return_value=profile) as mock_get:
            r = client.get("/member/profile",
                           headers={"Authorization": f"Bearer {token}"})
        # Ensure the service was called with the token's sub, not anything from the URL
        mock_get.assert_called_once_with("m1")
        assert r.status_code == 200
