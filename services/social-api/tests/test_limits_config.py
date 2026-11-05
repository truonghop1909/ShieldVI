from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from shieldvi_social.config import Settings
from shieldvi_social.main import create_app
from conftest import login, register


def test_auth_rate_limit_is_persistent_and_ignores_forwarded_ip(client, settings):
    limited = replace(settings, auth_rate_limit=2)
    with TestClient(create_app(limited)) as first:
        assert login(first, username="absent_user").status_code == 401
        assert login(first, username="absent_user").status_code == 401
    with TestClient(create_app(limited)) as restarted:
        response = restarted.post("/api/v1/auth/login", headers={"X-Forwarded-For": "203.0.113.1"},
            json={"username": "different_user", "password": "irrelevant"})
        assert response.status_code == 429
        assert int(response.headers["retry-after"]) > 0


def test_register_is_rate_limited(client, settings):
    with TestClient(create_app(replace(settings, auth_rate_limit=1))) as limited:
        assert register(limited).status_code == 201
        assert register(limited, username="fixture_two", email="two@example.com").status_code == 429


def test_account_limit_across_peers_and_window_reset(client, settings, monkeypatch):
    monkeypatch.setattr("shieldvi_social.rate_limit.time.time", lambda: 1800000000)
    app = create_app(replace(settings, auth_rate_limit=1))
    with TestClient(app, client=("198.51.100.1", 1234)) as first:
        assert login(first, username="shared_account").status_code == 401
    with TestClient(create_app(replace(settings, auth_rate_limit=1)), client=("198.51.100.2", 1234)) as second:
        assert login(second, username="shared_account").status_code == 429
        monkeypatch.setattr("shieldvi_social.rate_limit.time.time", lambda: 1800000061)
        assert login(second, username="shared_account").status_code == 401


@pytest.mark.parametrize("kwargs", [
    {"cors_origins": ("*",)}, {"cors_origins": ("http://localhost:5173/path",)},
    {"database_url": "sqlite:///relative.sqlite3"}, {"database_url": "sqlite:///:memory:"},
    {"database_url": "sqlite:///E:/private/shieldvi_reviews.sqlite3"},
    {"session_ttl_seconds": 0}, {"auth_rate_limit": 0},
])
def test_unsafe_config_rejected(kwargs):
    with pytest.raises(ValueError):
        Settings(**kwargs)


def test_env_parsing_and_invalid_boolean(monkeypatch, tmp_path):
    monkeypatch.setenv("SOCIAL_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("SOCIAL_SESSION_TTL_SECONDS", "900")
    monkeypatch.setenv("SOCIAL_DATABASE_URL", f"sqlite:///{(tmp_path / 'social.sqlite3').as_posix()}")
    settings = Settings.from_env()
    assert settings.registration_enabled and settings.session_ttl_seconds == 900
    monkeypatch.setenv("SOCIAL_REGISTRATION_ENABLED", "maybe")
    with pytest.raises(ValueError):
        Settings.from_env()
