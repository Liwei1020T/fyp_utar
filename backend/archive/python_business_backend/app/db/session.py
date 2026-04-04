from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.database_url,
    echo=settings.sqlalchemy_echo,
    connect_args=_connect_args(settings.database_url),
    pool_pre_ping=not settings.database_url.startswith("sqlite"),
)
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)


def check_database_connection(db: Session) -> None:
    db.execute(text("SELECT 1")).scalar_one()


def create_all_tables() -> None:
    import app.db.models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def drop_all_tables() -> None:
    import app.db.models  # noqa: F401

    Base.metadata.drop_all(bind=engine)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
