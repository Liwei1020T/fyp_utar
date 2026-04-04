from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from stringsense_backend.db.models import StringCatalogItem
from stringsense_backend.db.models import User
from stringsense_backend.db.session import check_database_connection


def health_payload(db: Session) -> dict[str, object]:
    check_database_connection(db)
    string_count = db.execute(
        select(func.count()).select_from(StringCatalogItem)
    ).scalar_one()
    user_count = db.execute(select(func.count()).select_from(User)).scalar_one()
    return {
        "status": "ok",
        "service": "unified_python_backend",
        "strings": string_count,
        "users": user_count,
    }
