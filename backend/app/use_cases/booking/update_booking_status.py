from __future__ import annotations

from dataclasses import dataclass

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
        changed_by_user_id: str | None,
        note: str | None,
    ) -> BookingRecord:
        booking = self.booking_repository.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        validate_status_transition(booking.status, next_status)
        return self.booking_repository.update_status(
            booking_id=booking_id,
            next_status=next_status,
            changed_by_user_id=changed_by_user_id,
            note=note.strip() if note else None,
        )

