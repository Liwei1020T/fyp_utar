from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import StoreBusinessHoursRecord
from app.ports.repositories.store_repository import StoreRepository
from app.shared.errors import NotFoundError


@dataclass
class GetBusinessHoursUseCase:
    store_repository: StoreRepository

    def execute(self) -> StoreBusinessHoursRecord:
        hours = self.store_repository.get_business_hours()
        if hours is None:
            raise NotFoundError("Store business hours not found")
        return hours
