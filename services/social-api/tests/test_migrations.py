from io import StringIO
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from fastapi.testclient import TestClient
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from shieldvi_social.db import make_engine, session_factory
from shieldvi_social.main import create_app
from shieldvi_social.models import AuthSession, Base, Comment, Post, User
from conftest import migrate


def test_migration_upgrade_downgrade_and_metadata_match(settings):
    engine = make_engine(settings)
    try:
        migrate(engine)
        with engine.connect() as connection:
            assert compare_metadata(MigrationContext.configure(connection), Base.metadata) == []
        with session_factory(engine).begin() as db:
            db.add(User(id="fixture-id", username="fixture", email="fixture@example.com", password_hash="fixture-hash"))
        migrate(engine)  # No-op upgrade must retain identities.
        with session_factory(engine)() as db:
            assert db.get(User, "fixture-id") is not None
        migrate(engine, "downgrade", "base")  # Only synthetic temporary DB.
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
        migrate(engine)
        assert "users" in inspect(engine).get_table_names()
    finally:
        engine.dispose()


@pytest.mark.parametrize("role,status", [("owner", "active"), ("user", "unknown")])
def test_db_rejects_invalid_roles_and_status(settings, role, status):
    engine = make_engine(settings)
    try:
        migrate(engine)
        with pytest.raises(IntegrityError), session_factory(engine).begin() as db:
            db.add(User(username="fixture", email="fixture@example.com", password_hash="fixture-hash", role=role, status=status))
    finally:
        engine.dispose()


def test_foreign_key_enforced(settings):
    engine = make_engine(settings)
    try:
        migrate(engine)
        with pytest.raises(IntegrityError), session_factory(engine).begin() as db:
            db.add(AuthSession(token_hash="a" * 64, user_id="missing", created_at=1, expires_at=2))
    finally:
        engine.dispose()


def test_unmigrated_db_does_not_auto_create_user_schema(settings):
    app = create_app(settings)
    with pytest.raises(RuntimeError, match="unmigrated"):
        with TestClient(app):
            pass
    assert "users" not in inspect(app.state.engine).get_table_names()


def test_old_or_unknown_schema_revision_refuses_startup(client, settings):
    with client.app.state.engine.begin() as connection:
        connection.execute(text("UPDATE alembic_version SET version_num='unknown_revision'"))
    with pytest.raises(RuntimeError, match="schema is not current"):
        with TestClient(create_app(settings)):
            pass


def test_postgres_offline_migration_sql(monkeypatch):
    # SQL compilation only, not a claim that a PostgreSQL server was tested.
    monkeypatch.setenv("SOCIAL_DATABASE_URL", "postgresql+psycopg://localhost/fixture_social")
    output = StringIO()
    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"), output_buffer=output)
    command.upgrade(config, "head", sql=True)
    sql = output.getvalue()
    assert "CREATE TABLE users" in sql
    assert "CREATE TABLE auth_sessions" in sql
    assert "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE" in sql
    assert "PRAGMA" not in sql
    assert "CREATE TABLE posts" in sql and "CREATE TABLE comments" in sql
    assert "FOREIGN KEY(parent_id, post_id) REFERENCES comments (id, post_id)" in sql


def test_t008_upgrade_preserves_users_and_sessions_and_content_rollback(settings):
    engine = make_engine(settings)
    sessions = session_factory(engine)
    try:
        migrate(engine, revision="0001_users")
        with sessions.begin() as db:
            db.add(User(id="fixture-preserved", username="fixture", email="fixture@example.com", password_hash="fixture-hash"))
            db.flush()
            db.add(AuthSession(token_hash="a" * 64, user_id="fixture-preserved", created_at=1, expires_at=9999999999))
        migrate(engine)
        with sessions.begin() as db:
            assert db.get(User, "fixture-preserved") is not None
            assert db.get(AuthSession, "a" * 64) is not None
            db.add(Post(id="post-fixture", author_id="fixture-preserved", body="Fixture", create_key="post-key", request_hash="h"))
            db.flush()
            db.add(Comment(id="parent-fixture", post_id="post-fixture", author_id="fixture-preserved", body="Parent", create_key="parent-key", request_hash="h"))
            db.flush()
            db.add(Comment(id="child-fixture", post_id="post-fixture", parent_id="parent-fixture", author_id="fixture-preserved", body="Child", create_key="child-key", request_hash="h", depth=1))
        migrate(engine, "downgrade", "0001_users")
        assert "posts" not in inspect(engine).get_table_names()
        with sessions() as db:
            assert db.get(User, "fixture-preserved") is not None
            assert db.get(AuthSession, "a" * 64) is not None
        migrate(engine)
    finally:
        engine.dispose()
