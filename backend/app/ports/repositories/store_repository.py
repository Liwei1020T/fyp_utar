from __future__ import annotations

from typing import Protocol

from app.domain.store.entities import StoreBusinessHoursRecord
from app.domain.store.entities import StoreSettingsRecord


class StoreRepository(Protocol):
    def get_business_hours(self) -> StoreBusinessHoursRecord | None: ...

    def update_business_hours(
        self,
        *,
        days: list[dict[str, object]],
        special_closed_dates: list[str],
    ) -> StoreBusinessHoursRecord: ...

    def get_store_settings(self) -> StoreSettingsRecord | None: ...

    def update_store_settings(
        self,
        values: dict[str, object],
    ) -> StoreSettingsRecord: ...
