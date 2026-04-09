from __future__ import annotations

from dataclasses import dataclass

from app.domain.store.entities import CheckInLookup
from app.domain.booking.policies import booking_order_code
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
        for booking in self.booking_repository.list_active_queue() + [
            booking
            for booking in self.booking_repository.list_all_for_analytics()
            if booking.status not in {"cancelled", "rejected", "completed"}
        ]:
            if (
                booking.id.upper() == normalized_reference
                or booking_order_code(booking.id) == normalized_reference
                or booking_check_in_reference(booking.id) == normalized_reference
            ):
                return CheckInLookup(
                    matched_by=(
                        "booking_id"
                        if booking_order_code(booking.id) == normalized_reference
                        or booking.id.upper() == normalized_reference
                        else "check_in_reference"
                    ),
                    booking=booking,
                )
        raise NotFoundError("Booking not found")
