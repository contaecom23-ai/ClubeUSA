from app.services.auth import create_access_token


class TestGetProfile:
    def test_returns_own_profile(self, client, mock_db, user_row, auth_headers):
        mock_db.get_user_by_id.return_value = user_row

        resp = client.get("/me", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == user_row["id"]
        assert data["email"] == user_row["email"]
        # password_hash must never appear in the response
        assert "password_hash" not in data

    def test_unauthenticated_returns_401(self, client, mock_db):
        resp = client.get("/me")
        assert resp.status_code in (401, 403)  # HTTPBearer version-dependent

    def test_invalid_token_returns_401(self, client, mock_db):
        resp = client.get("/me", headers={"Authorization": "Bearer not.a.valid.token"})
        assert resp.status_code in (401, 403)

    def test_cross_tenant_isolation(self, client, mock_db, user_row):
        """Token for user A cannot access user B's data."""
        user_b = {**user_row, "id": "user-id-2", "email": "maria@example.com"}

        # Token belongs to user-id-2 (user B)
        token_b = create_access_token(user_id="user-id-2", email="maria@example.com")

        # DB returns user B for that ID — correct isolation
        mock_db.get_user_by_id.return_value = user_b

        resp = client.get("/me", headers={"Authorization": f"Bearer {token_b}"})

        assert resp.status_code == 200
        # Must return B's data, not A's
        assert resp.json()["id"] == "user-id-2"
        # Verify the DB was queried with user B's ID, not user A's
        mock_db.get_user_by_id.assert_called_once_with("user-id-2")


class TestUpdateProfile:
    def test_update_allowed_fields(self, client, mock_db, user_row, auth_headers):
        updated = {**user_row, "phone": "11999990000", "zip_code": "10001"}
        mock_db.get_user_by_id.return_value = user_row
        mock_db.update_user_profile.return_value = updated

        resp = client.patch("/me", headers=auth_headers, json={"phone": "11999990000", "zip_code": "10001"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "11999990000"
        assert data["zip_code"] == "10001"

    def test_user_id_comes_from_token_not_body(self, client, mock_db, user_row, auth_headers):
        """Ensure the backend ignores any id in the body — user_id comes from token."""
        mock_db.get_user_by_id.return_value = user_row
        mock_db.update_user_profile.return_value = user_row

        # Send a body with an attempted id injection — FastAPI should ignore it (not in the schema)
        resp = client.patch("/me", headers=auth_headers, json={"city": "New York", "id": "attacker-id"})

        assert resp.status_code == 200
        # update_user_profile must be called with the token's user_id, never "attacker-id"
        call_kwargs = mock_db.update_user_profile.call_args
        assert call_kwargs.kwargs["user_id"] == user_row["id"]
        assert call_kwargs.kwargs["user_id"] != "attacker-id"

    def test_empty_patch_returns_current_profile(self, client, mock_db, user_row, auth_headers):
        mock_db.get_user_by_id.return_value = user_row

        resp = client.patch("/me", headers=auth_headers, json={})

        assert resp.status_code == 200
        mock_db.update_user_profile.assert_not_called()

    def test_xss_in_bio_rejected(self, client, mock_db, user_row, auth_headers):
        mock_db.get_user_by_id.return_value = user_row

        resp = client.patch("/me", headers=auth_headers, json={"bio": "<img src=x onerror=alert(1)>"})

        assert resp.status_code == 422

    def test_unauthenticated_patch_returns_401(self, client, mock_db):
        resp = client.patch("/me", json={"city": "Miami"})
        assert resp.status_code in (401, 403)
