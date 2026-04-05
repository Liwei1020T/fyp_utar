from __future__ import annotations

from sqlalchemy.orm import Session

from stringsense_backend.db.session import check_database_connection


def health_payload(db: Session) -> dict[str, object]:
    check_database_connection(db)
    return {"status": "ok", "service": "backend"}


__all__ = ["health_payload"]
