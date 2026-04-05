from __future__ import annotations

from typing import Protocol

from app.domain.catalog.entities import StringItem
from app.domain.catalog.policies import InventoryAvailability
from app.shared.pagination import Page


class CatalogRepository(Protocol):
    def get_by_id(
        self,
        string_id: str,
        *,
        include_inactive: bool = False,
    ) -> StringItem | None: ...

    def list_strings(
        self,
        *,
        is_active: bool | None,
        brand: str | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]: ...

    def list_inventory(
        self,
        *,
        brand: str | None,
        search: str | None,
        availability: InventoryAvailability | None,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]: ...

    def create(self, values: dict[str, object]) -> StringItem: ...

    def update(self, string_id: str, values: dict[str, object]) -> StringItem: ...

    def deactivate(self, string_id: str) -> StringItem: ...

    def update_inventory(self, string_id: str, values: dict[str, object]) -> StringItem: ...

    def list_active_catalog(self) -> list[StringItem]: ...

