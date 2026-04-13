from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError


@dataclass
class UpdateStringUseCase:
    catalog_repository: CatalogRepository

    def execute(self, *, string_id: str, values: dict[str, object]) -> StringItem:
        existing = self.catalog_repository.get_by_id(string_id, include_inactive=True)
        if existing is None:
            raise NotFoundError("String not found")
        return self.catalog_repository.update(string_id, values)
