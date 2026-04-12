from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import RecommendationMatrixInspectionRecord
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError


@dataclass(slots=True)
class GetRecommendationMatrixUseCase:
    catalog_repository: CatalogRepository

    def execute(self, string_id: str) -> RecommendationMatrixInspectionRecord:
        item = self.catalog_repository.get_recommendation_matrix(string_id)
        if item is None:
            raise NotFoundError("String not found")
        return item
