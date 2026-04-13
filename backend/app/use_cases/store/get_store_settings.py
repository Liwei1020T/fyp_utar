from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import StoreSettingsRecord
from app.ports.repositories.store_repository import StoreRepository
from app.shared.errors import NotFoundError


@dataclass
class GetStoreSettingsUseCase:
    store_repository: StoreRepository

    def execute(self) -> StoreSettingsRecord:
        settings = self.store_repository.get_store_settings()
        if settings is None:
            raise NotFoundError("Store settings not found")
        return settings
