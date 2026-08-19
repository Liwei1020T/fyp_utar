from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.booking.entities import BookingRecord
from app.domain.booking.enums import BookingStatus
from app.domain.store.policies import booking_slot_datetime_utc
from app.domain.store.policies import booking_slot_id_for_datetime
from app.domain.store.policies import normalize_datetime
from app.domain.store.policies import normalize_store_input_datetime
from app.domain.store.policies import parse_booking_slot_id
from app.domain.store.policies import slots_for_date
from app.domain.store.policies import weekday_name
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.catalog_repository import CatalogRepository
from app.ports.repositories.store_repository import StoreRepository
from app.ports.services.clock import Clock
from app.shared.errors import BadRequestError
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError


@dataclass
class CreateBookingUseCase:
    booking_repository: BookingRepository
    catalog_repository: CatalogRepository
    store_repository: StoreRepository
    clock: Clock
    store_timezone: str

    def execute(
        self,
        *,
        user_id: str,
        string_id: str,
        racket_id: str | None = None,
        racket_brand: str | None,
        racket_model: str | None,
        requested_tension: float | None,
        slot_id: str | None,
        drop_off_datetime: datetime | None,
        notes: str | None,
        service_method: str = "counter_dropoff",
    ) -> BookingRecord:
        string_item = self.catalog_repository.get_by_id(
            string_id, include_inactive=False
        )
        if string_item is None:
            raise NotFoundError("String not found")

        if racket_id is not None:
            racket_identity = self.booking_repository.get_owned_racket_identity(
                racket_id=racket_id,
                user_id=user_id,
            )
            if racket_identity is None:
                raise NotFoundError("Racket not found")
            racket_brand, racket_model = racket_identity

        resolved_drop_off = self._resolve_drop_off_datetime(
            slot_id=slot_id,
            drop_off_datetime=drop_off_datetime,
        )
        return self.booking_repository.create_booking(
            user_id=user_id,
            string_id=string_id,
            racket_id=racket_id,
            racket_brand=racket_brand,
            racket_model=racket_model,
            requested_tension=requested_tension,
            drop_off_datetime=resolved_drop_off,
            expected_completion_datetime=None,
            notes=notes,
            service_method=service_method,
            status=BookingStatus.AWAITING_DROPOFF.value,
            changed_by_user_id=user_id,
        )

    def _resolve_drop_off_datetime(
        self,
        *,
        slot_id: str | None,
        drop_off_datetime: datetime | None,
    ) -> datetime | None:
        if slot_id is None and drop_off_datetime is None:
            return None

        if drop_off_datetime is not None:
            local_drop_off = normalize_store_input_datetime(
                drop_off_datetime,
                self.store_timezone,
            )
            if local_drop_off.second != 0 or local_drop_off.microsecond != 0:
                raise BadRequestError("Drop-off time must align with a store slot")
            slot_id = booking_slot_id_for_datetime(
                drop_off_datetime,
                self.store_timezone,
            )

        assert slot_id is not None
        local_slot_datetime = parse_booking_slot_id(slot_id)
        if local_slot_datetime is None:
            raise BadRequestError("Invalid booking slot id")

        local_now = normalize_datetime(self.clock.now(), self.store_timezone)
        assert local_now is not None
        if local_slot_datetime <= local_now:
            raise BadRequestError("Drop-off slot must be in the future")

        self.booking_repository.lock_slot_capacity()
        hours = self.store_repository.get_business_hours()
        if hours is None:
            raise NotFoundError("Store business hours not found")
        bookings = self.booking_repository.list_slot_bookings()
        day_config = next(
            (
                day
                for day in hours.days
                if day.day == weekday_name(local_slot_datetime.date())
            ),
            None,
        )
        slots = slots_for_date(
            target_date=local_slot_datetime.date(),
            day_config=day_config,
            special_closed_dates=hours.special_closed_dates,
            bookings=bookings,
            timezone_name=self.store_timezone,
            not_before=local_now,
        )
        selected_slot = next((item for item in slots if item.id == slot_id), None)
        if selected_slot is None:
            raise BadRequestError("Drop-off slot is not offered by the store")
        if selected_slot.available_spots < 1:
            raise ConflictError("Drop-off slot is fully booked")
        return booking_slot_datetime_utc(local_slot_datetime, self.store_timezone)
