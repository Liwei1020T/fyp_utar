from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringOfficialPerformance
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError


@dataclass
class GetOfficialPerformanceUseCase:
    catalog_repository: CatalogRepository

    def execute(self, *, string_id: str) -> StringOfficialPerformance:
        item = self.catalog_repository.get_official_performance(string_id)
        if item is None:
            raise NotFoundError("Official performance record not found")
        return item
