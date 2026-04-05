from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from alembic.script.base import Script
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.adapters.persistence.sqlalchemy.base import Base
from app.config.settings import get_settings
import app.adapters.persistence.sqlalchemy.models  # noqa: F401


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", get_settings().sqlalchemy_database_url)
target_metadata = Base.metadata


_original_list_py_dir = Script._list_py_dir


@classmethod
def _filtered_list_py_dir(cls, scriptdir, path):
    paths = _original_list_py_dir(scriptdir, path)
    return [
        candidate
        for candidate in paths
        if not candidate.name.startswith("._") and not candidate.name.startswith(".__")
    ]


Script._list_py_dir = _filtered_list_py_dir


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
