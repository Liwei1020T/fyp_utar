from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.domain.catalog.entities import RecommendationMatrixImportReport
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import BadRequestError


@dataclass(slots=True)
class ImportRecommendationMatrixUseCase:
    catalog_repository: CatalogRepository
    matrix_path: Path

    def execute(self) -> RecommendationMatrixImportReport:
        if not self.matrix_path.exists():
            raise BadRequestError(
                f"Recommendation matrix artifact not found: {self.matrix_path}"
            )
        return self.catalog_repository.import_recommendation_matrix(self.matrix_path)
