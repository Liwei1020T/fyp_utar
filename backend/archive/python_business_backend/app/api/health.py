from __future__ import annotations

from sqlalchemy.orm import Session

from app.db.session import check_database_connection


def health_payload(db: Session) -> dict[str, str]:
    check_database_connection(db)
    return {"status": "ok", "database": "ok"}
