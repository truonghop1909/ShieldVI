import pytest
from sqlalchemy import select

from shieldvi_social.models import User
from conftest import login, register


@pytest.mark.parametrize("role,status", [("user", 403), ("moderator", 403), ("admin", 200)])
def test_admin_route_checks_current_db_role(authenticated, role, status):
    client, headers = authenticated
    with client.app.state.sessions.begin() as db:
        db.scalar(select(User)).role = role  # Synthetic provisioning only in temporary DB.
    response = client.get("/api/v1/admin/access", headers=headers)
    assert response.status_code == status
    if role == "admin":
        with client.app.state.sessions.begin() as db:
            db.scalar(select(User)).role = "user"
        assert client.get("/api/v1/admin/access", headers=headers).status_code == 403


def test_role_header_and_login_extra_field_cannot_grant_admin(authenticated):
    client, headers = authenticated
    assert client.get("/api/v1/admin/access", headers={**headers, "X-Role": "admin"}).status_code == 403
    assert client.post("/api/v1/auth/login", json={"username": "fixture_user",
        "password": "synthetic-test-password-123", "role": "admin"}).status_code == 422


def test_me_cannot_select_someone_else(authenticated):
    client, headers = authenticated
    first = client.get("/api/v1/me", headers=headers).json()
    other = register(client, username="fixture_two", email="two@example.com").json()
    response = client.get("/api/v1/me", params={"user_id": other["id"]}, headers=headers)
    assert response.json()["id"] == first["id"]
    assert response.json()["id"] != other["id"]
    assert "email" not in response.json()


def test_sessions_are_distinct_and_logout_only_revokes_current(authenticated):
    client, first = authenticated
    token = login(client).json()["access_token"]
    second = {"Authorization": "Bearer " + token}
    assert first != second
    assert client.post("/api/v1/auth/logout", headers=first).status_code == 204
    assert client.get("/api/v1/me", headers=second).status_code == 200
