from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError


@dataclass
class UpdateInventoryStringUseCase:
    catalog_repository: CatalogRepository

    def execute(self, *, string_id: str, values: dict[str, object]) -> StringItem:
        if not values:
            raise BadRequestError("At least one inventory field must be provided")
        existing = self.catalog_repository.get_by_id(string_id, include_inactive=True)
        if existing is None:
            raise NotFoundError("String not found")
        return self.catalog_repository.update_inventory(string_id, values)

