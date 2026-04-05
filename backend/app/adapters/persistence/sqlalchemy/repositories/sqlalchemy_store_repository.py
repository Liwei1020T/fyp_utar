from __future__ import annotations

from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import StoreBusinessHours
from app.adapters.persistence.sqlalchemy.models import StoreSettings
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_business_hours
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_store_settings
from app.domain.store.entities import StoreBusinessHoursRecord
from app.domain.store.entities import StoreSettingsRecord
from app.shared.constants import STORE_ID


class SqlAlchemyStoreRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_business_hours(self) -> StoreBusinessHoursRecord | None:
        record = self.db.get(StoreBusinessHours, STORE_ID)
        return to_business_hours(record) if record else None

    def update_business_hours(
        self,
        *,
        days: list[dict[str, object]],
        special_closed_dates: list[str],
    ) -> StoreBusinessHoursRecord:
        record = self.db.get(StoreBusinessHours, STORE_ID)
        assert record is not None
        record.days_json = days
        record.special_closed_dates = special_closed_dates
        self.db.commit()
        self.db.refresh(record)
        return to_business_hours(record)

    def get_store_settings(self) -> StoreSettingsRecord | None:
        record = self.db.get(StoreSettings, STORE_ID)
        return to_store_settings(record) if record else None

    def update_store_settings(
        self,
        values: dict[str, object],
    ) -> StoreSettingsRecord:
        record = self.db.get(StoreSettings, STORE_ID)
        assert record is not None
        for field, value in values.items():
            setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return to_store_settings(record)

