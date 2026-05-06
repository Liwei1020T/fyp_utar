from __future__ import annotations

from dataclasses import dataclass

from app.domain.booking.entities import BookingRecord
from app.domain.booking.enums import BookingStatus
from app.domain.booking.policies import validate_status_transition
from app.ports.repositories.booking_repository import BookingRepository
from app.shared.errors import ConflictError
from app.use_cases.store.lookup_checkin import LookupCheckInUseCase


@dataclass
class ConfirmCheckInUseCase:
    booking_repository: BookingRepository
    lookup_check_in_use_case: LookupCheckInUseCase

    def execute(
        self,
        *,
        booking_id: str | None,
        reference: str | None,
        admin_user_id: str,
        note: str | None,
    ) -> BookingRecord:
        lookup = self.lookup_check_in_use_case.execute(
            booking_id=booking_id,
            reference=reference,
        )
        booking = lookup.booking
        if booking.status != BookingStatus.AWAITING_DROPOFF.value:
            raise ConflictError("Only awaiting drop-off bookings can be checked in")
        next_status = BookingStatus.IN_PROGRESS.value
        validate_status_transition(booking.status, next_status)
        return self.booking_repository.update_status(
            booking_id=booking.id,
            next_status=next_status,
            expected_completion_datetime=None,
            update_expected_completion_datetime=False,
            changed_by_user_id=admin_user_id,
            note=(note or "Checked in at the service counter.").strip(),
        )
