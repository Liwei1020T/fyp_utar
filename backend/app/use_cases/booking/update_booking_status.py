from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.domain.booking.entities import BookingRecord
from app.domain.booking.policies import validate_status_transition
from app.domain.booking.policies import validate_terminal_status_note
from app.ports.repositories.booking_repository import BookingRepository
from app.ports.transaction_manager import TransactionManager
from app.shared.errors import NotFoundError


@dataclass
class UpdateBookingStatusUseCase:
    booking_repository: BookingRepository
    transaction_manager: TransactionManager

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
        try:
            booking = self.booking_repository.get_by_id_for_update(booking_id)
            if booking is None:
                raise NotFoundError("Booking not found")

            normalized_note = note.strip() if note else None
            status_changed = next_status != booking.status
            if status_changed:
                validate_status_transition(booking.status, next_status)
                validate_terminal_status_note(next_status, normalized_note)
            updated = self.booking_repository.update_status(
                booking_id=booking_id,
                next_status=next_status,
                expected_completion_datetime=expected_completion_datetime,
                update_expected_completion_datetime=update_expected_completion_datetime,
                changed_by_user_id=changed_by_user_id,
                note=normalized_note,
                commit=False,
            )
            self.transaction_manager.commit()
            return updated
        except Exception:
            self.transaction_manager.rollback()
            raise
