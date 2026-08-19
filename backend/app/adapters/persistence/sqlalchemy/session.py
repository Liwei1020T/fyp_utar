from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.adapters.persistence.sqlalchemy.base import Base
from app.config.settings import get_settings
from app.shared.transaction_effects import commit_transaction_effects
from app.shared.transaction_effects import rollback_transaction_effects


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


settings = get_settings()
engine = create_engine(
    settings.sqlalchemy_database_url,
    connect_args=_connect_args(settings.sqlalchemy_database_url),
    pool_pre_ping=not settings.sqlalchemy_database_url.startswith("sqlite"),
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def create_all_tables() -> None:
    import app.adapters.persistence.sqlalchemy.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    import app.adapters.persistence.sqlalchemy.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)


def check_database_connection(db: Session) -> None:
    db.execute(text("SELECT 1")).scalar_one()


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    except BaseException:
        try:
            db.rollback()
        finally:
            rollback_transaction_effects(db)
        raise
    else:
        try:
            db.commit()
        except BaseException:
            try:
                db.rollback()
            finally:
                rollback_transaction_effects(db)
            raise
        commit_transaction_effects(db)
    finally:
        db.close()
