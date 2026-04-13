from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository


@dataclass
class CreateStringUseCase:
    catalog_repository: CatalogRepository

    def execute(self, values: dict[str, object]) -> StringItem:
        return self.catalog_repository.create(values)
