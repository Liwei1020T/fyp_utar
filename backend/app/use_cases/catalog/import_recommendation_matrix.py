from __future__ import annotations

from dataclasses import dataclass

from app.config.settings import get_settings
from app.domain.catalog.entities import RecommendationMatrixImportReport
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import BadRequestError


@dataclass(slots=True)
class ImportRecommendationMatrixUseCase:
    catalog_repository: CatalogRepository

    def execute(self) -> RecommendationMatrixImportReport:
        matrix_path = get_settings().recommendation_matrix_path
        if not matrix_path.exists():
            raise BadRequestError(
                f"Recommendation matrix artifact not found: {matrix_path}"
            )
        return self.catalog_repository.import_recommendation_matrix()
