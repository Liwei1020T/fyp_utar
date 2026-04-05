from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import StoreSettingsRecord
from app.ports.repositories.store_repository import StoreRepository


@dataclass
class UpdateStoreSettingsUseCase:
    store_repository: StoreRepository

    def execute(self, values: dict[str, object]) -> StoreSettingsRecord:
        return self.store_repository.update_store_settings(values)

