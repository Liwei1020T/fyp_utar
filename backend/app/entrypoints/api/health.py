from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    recommendation_matrix_source_generated_at,
)
from app.adapters.persistence.sqlalchemy.recommendation_matrix_import import (
    recommendation_matrix_source_version,
)
from app.adapters.persistence.sqlalchemy.session import check_database_connection
from app.config.settings import get_settings


def health_payload(db: Session) -> dict[str, object]:
    check_database_connection(db)
    artifact_path = get_settings().recommendation_matrix_path
    if not artifact_path.is_file():
        raise HTTPException(
            status_code=503,
            detail="Canonical recommendation matrix artifact is missing",
        )
    generated_at = recommendation_matrix_source_generated_at(artifact_path)
    return {
        "status": "ok",
        "service": "backend",
        "recommendation_artifact": {
            "source_version": recommendation_matrix_source_version(artifact_path),
            "source_generated_at": generated_at.isoformat() if generated_at else None,
        },
    }
