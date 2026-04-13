from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError


@dataclass
class GetStringUseCase:
    catalog_repository: CatalogRepository

    def execute(self, *, string_id: str, include_inactive: bool = False) -> StringItem:
        item = self.catalog_repository.get_by_id(
            string_id,
            include_inactive=include_inactive,
        )
        if item is None:
            raise NotFoundError("String not found")
        return item
