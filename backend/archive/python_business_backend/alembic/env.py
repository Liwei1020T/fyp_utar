from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from alembic.script.base import Script
from sqlalchemy import engine_from_config
from sqlalchemy import pool

from app.core.config import settings
from app.db.base import Base
import app.db.models  # noqa: F401


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata

_original_list_py_dir = Script._list_py_dir


@classmethod
def _list_py_dir_without_appledouble(cls, scriptdir, path):
    return [
        file_path
        for file_path in _original_list_py_dir(scriptdir, path)
        if not file_path.name.startswith("._")
    ]


Script._list_py_dir = _list_py_dir_without_appledouble


def run_migrations_offline() -> None:
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
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
