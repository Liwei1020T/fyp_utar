from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.store.entities import BookingSlot
from app.domain.store.policies import slots_for_date
from app.domain.store.policies import normalize_datetime
from app.domain.store.policies import weekday_name
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.store_repository import StoreRepository
from app.ports.services.clock import Clock
from app.shared.errors import NotFoundError
from app.shared.pagination import Page


@dataclass
class ListSlotsUseCase:
    store_repository: StoreRepository
    booking_repository: BookingRepository
    clock: Clock
    store_timezone: str

    def execute(
        self,
        *,
        date_value: date | None,
        date_from: date | None,
        days: int,
    ) -> Page[BookingSlot]:
        hours = self.store_repository.get_business_hours()
        if hours is None:
            raise NotFoundError("Store business hours not found")
        bookings = self.booking_repository.list_slot_bookings()
        local_now = normalize_datetime(self.clock.now(), self.store_timezone)
        assert local_now is not None

        if date_value is not None:
            day_config = next(
                (day for day in hours.days if day.day == weekday_name(date_value)),
                None,
            )
            slot_items = slots_for_date(
                target_date=date_value,
                day_config=day_config,
                special_closed_dates=hours.special_closed_dates,
                bookings=bookings,
                timezone_name=self.store_timezone,
                not_before=local_now,
            )
            return Page(items=slot_items, total=len(slot_items), limit=None, offset=0)

        start_date = max(date_from or local_now.date(), local_now.date())
        items: list[BookingSlot] = []
        for day_offset in range(days):
            target_date = start_date.fromordinal(start_date.toordinal() + day_offset)
            day_config = next(
                (day for day in hours.days if day.day == weekday_name(target_date)),
                None,
            )
            items.extend(
                slots_for_date(
                    target_date=target_date,
                    day_config=day_config,
                    special_closed_dates=hours.special_closed_dates,
                    bookings=bookings,
                    timezone_name=self.store_timezone,
                    not_before=local_now,
                )
            )
        return Page(items=items, total=len(items), limit=None, offset=0)
