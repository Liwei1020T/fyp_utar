from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError


@dataclass
class UpdateStringEditorUseCase:
    catalog_repository: CatalogRepository

    def execute(
        self,
        *,
        string_id: str,
        catalog_values: dict[str, object],
        inventory_values: dict[str, object],
        official_performance_values: dict[str, object],
    ) -> StringItem:
        if not any((catalog_values, inventory_values, official_performance_values)):
            raise BadRequestError("At least one editor field must be provided")
        existing = self.catalog_repository.get_by_id(
            string_id,
            include_inactive=True,
        )
        if existing is None:
            raise NotFoundError("String not found")
        return self.catalog_repository.update_editor(
            string_id,
            catalog_values=catalog_values,
            inventory_values=inventory_values,
            official_performance_values=official_performance_values,
        )
