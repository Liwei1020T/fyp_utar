from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import InventoryMovementRecord
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError
from app.shared.pagination import Page


@dataclass
class ListInventoryMovementsUseCase:
    catalog_repository: CatalogRepository

    def execute(
        self,
        *,
        string_id: str,
        limit: int | None,
        offset: int,
    ) -> Page[InventoryMovementRecord]:
        if self.catalog_repository.get_by_id(string_id, include_inactive=True) is None:
            raise NotFoundError("String not found")
        return self.catalog_repository.list_inventory_movements(
            string_id,
            limit=limit,
            offset=offset,
        )
