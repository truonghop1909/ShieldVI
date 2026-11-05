from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .config import Settings


def make_engine(settings: Settings):
    kwargs = {"pool_pre_ping": True, "hide_parameters": True}
    if settings.database_url.startswith("sqlite:"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 20}
    engine = create_engine(settings.database_url, **kwargs)
    if engine.dialect.name == "sqlite":
        Path(engine.url.database).parent.mkdir(parents=True, exist_ok=True)

        @event.listens_for(engine, "connect")
        def sqlite_connect(connection, _):
            connection.isolation_level = None
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA busy_timeout=20000")

        @event.listens_for(engine, "begin")
        def sqlite_begin(connection):
            connection.exec_driver_sql("BEGIN IMMEDIATE" if connection.get_execution_options().get("sqlite_immediate") else "BEGIN")

    return engine


def session_factory(engine):
    return sessionmaker(bind=engine, expire_on_commit=False)
