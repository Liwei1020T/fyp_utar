from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import StoreBusinessHoursRecord
from app.ports.repositories.store_repository import StoreRepository


@dataclass
class UpdateBusinessHoursUseCase:
    store_repository: StoreRepository

    def execute(
        self,
        *,
        days: list[dict[str, object]],
        special_closed_dates: list[str],
    ) -> StoreBusinessHoursRecord:
        return self.store_repository.update_business_hours(
            days=days,
            special_closed_dates=special_closed_dates,
        )
