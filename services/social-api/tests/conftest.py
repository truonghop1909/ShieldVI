from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from shieldvi_social.config import Settings
from shieldvi_social.db import make_engine
from shieldvi_social.main import create_app

ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "synthetic-test-password-123"


def migrate(engine, direction="upgrade", revision="head"):
    config = Config(str(ROOT / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        getattr(command, direction)(config, revision)


@pytest.fixture
def settings(tmp_path):
    return Settings(database_url=f"sqlite:///{(tmp_path / 'social-test.sqlite3').as_posix()}",
                    registration_enabled=True, auth_rate_limit=100,
                    cors_origins=("http://localhost:5173",))


@pytest.fixture
def client(settings):
    engine = make_engine(settings)
    migrate(engine)
    engine.dispose()
    app = create_app(settings)
    with TestClient(app) as client:
        yield client


def register(client, username="fixture_user", email="fixture@example.com", **overrides):
    return client.post("/api/v1/auth/register", json={
        "username": username, "email": email, "password": PASSWORD, **overrides,
    })


def login(client, username="fixture_user", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"username": username, "password": password})


@pytest.fixture
def authenticated(client):
    assert register(client).status_code == 201
    response = login(client)
    assert response.status_code == 200, response.text
    return client, {"Authorization": "Bearer " + response.json()["access_token"]}
