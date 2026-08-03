from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    recommendation_matrix_source_version,
)
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.adapters.persistence.sqlalchemy.session import check_database_connection
from app.config.settings import get_settings


def health_payload(db: Session) -> dict[str, object]:
    check_database_connection(db)
    configured_path = get_settings().recommendation_matrix_path
    configured_source_version = (
        recommendation_matrix_source_version(configured_path)
        if configured_path.is_file()
        else None
    )
    artifact = db.execute(
        select(
            StringRecommendationMatrix.source_version,
            StringRecommendationMatrix.source_generated_at,
        )
        .where(
            StringRecommendationMatrix.source_layer == "nlp_review",
            StringRecommendationMatrix.source_version.is_not(None),
        )
        .order_by(StringRecommendationMatrix.updated_at.desc())
        .limit(1)
    ).one_or_none()
    if artifact is None:
        artifact_status = "catalog_fallback"
    elif artifact.source_version == configured_source_version:
        artifact_status = "imported"
    else:
        artifact_status = "stale"
    return {
        "status": "ok",
        "service": "backend",
        "recommendation_artifact": {
            "status": artifact_status,
            "source_version": artifact.source_version if artifact else None,
            "source_generated_at": (
                artifact.source_generated_at.isoformat()
                if artifact and artifact.source_generated_at
                else None
            ),
        },
    }
