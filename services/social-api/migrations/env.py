from alembic import context

from shieldvi_social.config import Settings
from shieldvi_social.db import make_engine
from shieldvi_social.models import Base

config = context.config
target_metadata = Base.metadata


def run(connection):
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True,
                      render_as_batch=connection.dialect.name == "sqlite")
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    context.configure(url=Settings.from_env().database_url, target_metadata=target_metadata,
                      literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()
elif config.attributes.get("connection") is not None:
    run(config.attributes["connection"])
else:
    engine = make_engine(Settings.from_env())
    try:
        with engine.connect() as connection:
            run(connection)
    finally:
        engine.dispose()
