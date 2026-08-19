from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.session import check_database_connection


def health_payload(db: Session) -> dict[str, object]:
    check_database_connection(db)
    artifact_rows = db.scalar(
        select(func.count())
        .select_from(StringRecommendationMatrix)
        .where(StringRecommendationMatrix.source_layer == "nlp_review")
    )
    return {
        "status": "ok",
        "service": "backend",
        "recommendation_artifact": {
            "status": "imported" if artifact_rows else "catalog_fallback",
            "rows": artifact_rows or 0,
        },
    }
