from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import CheckInLookup
from app.domain.store.policies import booking_check_in_reference
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.errors import NotFoundError


@dataclass
class LookupCheckInUseCase:
    booking_repository: BookingRepository

    def execute(
        self,
        *,
        booking_id: str | None,
        reference: str | None,
    ) -> CheckInLookup:
        if booking_id:
            booking = self.booking_repository.get_by_id(
                booking_id
            ) or self.booking_repository.get_by_order_code(booking_id)
            if booking is None:
                raise NotFoundError("Booking not found")
            return CheckInLookup(matched_by="booking_id", booking=booking)

        assert reference is not None
        normalized_reference = reference.strip().upper()
        booking = self.booking_repository.find_active_by_reference(normalized_reference)
        if booking is not None:
            matched_by_check_in_reference = (
                booking_check_in_reference(booking.id) == normalized_reference
                or normalized_reference.startswith("LIVE-")
            )
            return CheckInLookup(
                matched_by=(
                    "check_in_reference"
                    if matched_by_check_in_reference
                    else "booking_id"
                ),
                booking=booking,
            )
        raise NotFoundError("Booking not found")
