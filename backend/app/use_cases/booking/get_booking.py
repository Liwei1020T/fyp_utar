from __future__ import annotations

from dataclasses import dataclass

from app.domain.booking.entities import BookingRecord
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.errors import NotFoundError


@dataclass
class GetBookingUseCase:
    booking_repository: BookingRepository

    def execute(self, booking_id: str) -> BookingRecord:
        booking = self.booking_repository.get_by_id(booking_id)
        if booking is None:
            raise NotFoundError("Booking not found")
        return booking
