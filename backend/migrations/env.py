from __future__ import annotations

from logging.config import fileConfig

from alembic import context
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

ALEMBIC_IGNORED_TABLES = {"string_catalog_items_legacy"}


def include_object(object_, name, type_, reflected, compare_to) -> bool:
    if type_ == "table" and name in ALEMBIC_IGNORED_TABLES:
        return False

    parent_table = getattr(object_, "table", None)
    if parent_table is not None and parent_table.name in ALEMBIC_IGNORED_TABLES:
        return False

    if type_ == "foreign_key_constraint":
        referred_tables = {
            element.column.table.name
            for element in getattr(object_, "elements", [])
            if getattr(element, "column", None) is not None
        }
        if referred_tables & ALEMBIC_IGNORED_TABLES:
            return False

    return True


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
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
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
