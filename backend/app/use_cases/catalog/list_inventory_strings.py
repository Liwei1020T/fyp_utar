from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.domain.catalog.policies import InventoryAvailability
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.pagination import Page


@dataclass
class ListInventoryStringsUseCase:
    catalog_repository: CatalogRepository

    def execute(
        self,
        *,
        brand: str | None,
        search: str | None,
        availability: InventoryAvailability | None,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]:
        return self.catalog_repository.list_inventory(
            brand=brand,
            search=search,
            availability=availability,
            limit=limit,
            offset=offset,
        )
