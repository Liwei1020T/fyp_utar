from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.pagination import Page


@dataclass
class ListStringsUseCase:
    catalog_repository: CatalogRepository

    def execute(
        self,
        *,
        is_active: bool | None,
        brand: str | None,
        series: str | None,
        gauge_min: float | None,
        gauge_max: float | None,
        is_hybrid: bool | None,
        search: str | None,
        sort_by: str,
        sort_order: str,
        limit: int | None,
        offset: int,
    ) -> Page[StringItem]:
        return self.catalog_repository.list_strings(
            is_active=is_active,
            brand=brand,
            series=series,
            gauge_min=gauge_min,
            gauge_max=gauge_max,
            is_hybrid=is_hybrid,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
