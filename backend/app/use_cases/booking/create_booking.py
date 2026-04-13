from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.booking.entities import BookingRecord
from app.domain.booking.enums import BookingStatus
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.repositories.catalog_repository import CatalogRepository
from app.shared.errors import NotFoundError


@dataclass
class CreateBookingUseCase:
    booking_repository: BookingRepository
    catalog_repository: CatalogRepository

    def execute(
        self,
        *,
        user_id: str,
        string_id: str,
        racket_brand: str | None,
        racket_model: str | None,
        requested_tension: float | None,
        drop_off_datetime: datetime | None,
        notes: str | None,
    ) -> BookingRecord:
        string_item = self.catalog_repository.get_by_id(
            string_id, include_inactive=False
        )
        if string_item is None:
            raise NotFoundError("String not found")
        return self.booking_repository.create_booking(
            user_id=user_id,
            string_id=string_id,
            racket_brand=racket_brand,
            racket_model=racket_model,
            requested_tension=requested_tension,
            drop_off_datetime=drop_off_datetime,
            notes=notes,
            status=BookingStatus.AWAITING_DROPOFF.value,
            changed_by_user_id=user_id,
        )
