from logging.config import fileConfig

from alembic import context
from flask import current_app

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

migrate_extension = current_app.extensions["migrate"]
db = migrate_extension.db
engine = db.engine
target_metadata = db.metadata
config.set_main_option("sqlalchemy.url", str(engine.url).replace("%", "%%"))


def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
