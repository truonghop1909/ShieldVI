import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from argon2 import PasswordHasher
from fastapi.testclient import TestClient
from sqlalchemy import select

from shieldvi_social.main import create_app
from shieldvi_social.config import Settings
from shieldvi_social.models import AuthSession, User
from shieldvi_social.security import PASSWORD_HASHER, token_digest
from conftest import PASSWORD, login, register


def test_register_login_me_logout_stores_only_hashes(client):
    response = register(client, username=" Fixture_User ", email="FIXTURE@EXAMPLE.COM")
    assert response.status_code == 201, response.text
    user_id = response.json()["id"]
    assert set(response.json()) == {"id", "username", "role", "status", "created_at"}
    assert response.json()["username"] == "fixture_user"
    assert response.json()["role"] == "user"
    with client.app.state.sessions() as db:
        user = db.get(User, user_id)
        assert user.password_hash.startswith("$argon2id$")
        assert PASSWORD not in user.password_hash
        assert PASSWORD_HASHER.verify(user.password_hash, PASSWORD)
        assert user.email == "fixture@example.com"
    result = login(client, username="FIXTURE_USER")
    assert result.status_code == 200
    token = result.json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    with client.app.state.sessions() as db:
        session = db.scalar(select(AuthSession))
        assert session.token_hash == token_digest(token)
        assert session.token_hash != token
        assert session.expires_at - session.created_at == 3600
    me = client.get("/api/v1/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["id"] == user_id
    assert me.headers["cache-control"] == "no-store"
    assert "set-cookie" not in result.headers
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_password_salts_differ(client):
    assert register(client).status_code == 201
    assert register(client, username="fixture_two", email="two@example.com").status_code == 201
    with client.app.state.sessions() as db:
        hashes = db.scalars(select(User.password_hash)).all()
    assert len(set(hashes)) == 2


def test_concurrent_register_has_one_identity(client):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: register(client), range(2)))
    assert sorted(result.status_code for result in results) == [201, 409]
    with client.app.state.sessions() as db:
        assert len(db.scalars(select(User)).all()) == 1


@pytest.mark.parametrize("duplicate", [
    {"username": "FIXTURE_USER", "email": "other@example.com"},
    {"username": "another", "email": "FIXTURE@EXAMPLE.COM"},
])
def test_duplicate_identity_is_case_insensitive_and_generic(client, duplicate):
    assert register(client).status_code == 201
    response = register(client, **duplicate)
    assert response.status_code == 409
    assert response.json() == {"detail": "Account could not be registered"}
    assert PASSWORD not in response.text


@pytest.mark.parametrize("change", [
    {"password": "tinysecret"}, {"password": "x" * 129},
    {"email": "invalid-private-address"}, {"username": "<script>"},
    {"role": "admin"}, {"status": "active"}, {"password_hash": "injected"},
])
def test_invalid_registration_never_echoes_sensitive_values(client, change):
    response = register(client, **change)
    assert response.status_code == 422
    assert PASSWORD not in response.text
    for value in change.values():
        assert value not in response.text
    assert all("input" not in error and "ctx" not in error for error in response.json()["detail"])


def test_unknown_account_wrong_password_and_suspended_have_same_error(client):
    assert register(client).status_code == 201
    wrong = login(client, password="wrong-password")
    absent = login(client, username="unknown_user")
    with client.app.state.sessions.begin() as db:
        db.scalar(select(User)).status = "suspended"
    suspended = login(client)
    assert wrong.status_code == absent.status_code == suspended.status_code == 401
    assert wrong.json() == absent.json() == suspended.json()


@pytest.mark.parametrize("authorization", [None, "Basic YTpi", "Bearer forged", "Bearer " + "x" * 43])
def test_missing_or_invalid_bearer_is_rejected(client, authorization):
    headers = {"Authorization": authorization} if authorization else {}
    response = client.get("/api/v1/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_expired_session_rejected(authenticated):
    client, headers = authenticated
    with client.app.state.sessions.begin() as db:
        session = db.scalar(select(AuthSession))
        session.created_at = int(time.time()) - 7200
        session.expires_at = int(time.time()) - 1
    assert client.get("/api/v1/me", headers=headers).status_code == 401


def test_sessions_survive_restart_and_suspension_takes_effect(authenticated, settings):
    client, headers = authenticated
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get("/api/v1/me", headers=headers).status_code == 200
        with restarted.app.state.sessions.begin() as db:
            db.scalar(select(User)).status = "suspended"
        assert restarted.get("/api/v1/me", headers=headers).status_code == 401


def test_login_upgrades_outdated_password_parameters(client):
    assert register(client).status_code == 201
    old = PasswordHasher(time_cost=1, memory_cost=8192, parallelism=1).hash(PASSWORD)
    with client.app.state.sessions.begin() as db:
        db.scalar(select(User)).password_hash = old
    assert login(client).status_code == 200
    with client.app.state.sessions() as db:
        upgraded = db.scalar(select(User.password_hash))
    assert upgraded != old
    assert not PASSWORD_HASHER.check_needs_rehash(upgraded)


def test_registration_disabled_by_default(client, settings):
    with TestClient(create_app(replace(settings, registration_enabled=False))) as private:
        assert register(private).status_code == 403
    assert Settings().registration_enabled is False


def test_oversized_and_malformed_payload_do_not_echo_password(client):
    response = client.post("/api/v1/auth/login", content='{"password":"' + "s" * 20000 + '"}')
    assert response.status_code == 413
    malformed = client.post("/api/v1/auth/login", content='{"password":"sensitive-test-secret",',
                            headers={"Content-Type": "application/json"})
    assert malformed.status_code == 422
    assert "sensitive-test-secret" not in malformed.text


def test_cors_allowlist_and_no_cookie_credentials(client):
    allowed = client.options("/api/v1/me", headers={"Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"})
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-credentials" not in allowed.headers
    denied = client.options("/api/v1/me", headers={"Origin": "https://untrusted.invalid",
                                                "Access-Control-Request-Method": "GET"})
    assert denied.status_code == 400
    assert "access-control-allow-origin" not in denied.headers
