from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.booking.entities import BookingRecord
from app.domain.booking.policies import validate_status_transition
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.errors import NotFoundError


@dataclass
class UpdateBookingStatusUseCase:
    booking_repository: BookingRepository

    def execute(
        self,
        *,
        booking_id: str,
        next_status: str,
        expected_completion_datetime: datetime | None,
        update_expected_completion_datetime: bool,
        changed_by_user_id: str | None,
        note: str | None,
    ) -> BookingRecord:
        booking = self.booking_repository.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")

        status_changed = next_status != booking.status
        if status_changed:
            validate_status_transition(booking.status, next_status)
        return self.booking_repository.update_status(
            booking_id=booking_id,
            next_status=next_status,
            expected_completion_datetime=expected_completion_datetime,
            update_expected_completion_datetime=update_expected_completion_datetime,
            changed_by_user_id=changed_by_user_id,
            note=note.strip() if note else None,
        )
