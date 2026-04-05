from __future__ import annotations

from app.domain.booking.enums import BookingStatus
from app.shared.errors import ConflictError


BOOKING_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.AWAITING_DROPOFF: {
        BookingStatus.IN_PROGRESS,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.IN_PROGRESS: {
        BookingStatus.READY_FOR_COLLECTION,
        BookingStatus.CANCELLED,
    },
    BookingStatus.READY_FOR_COLLECTION: {BookingStatus.COMPLETED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.REJECTED: set(),
}


def validate_status_transition(current_status: str, next_status: str) -> None:
    current = BookingStatus(current_status)
    requested = BookingStatus(next_status)
    if requested not in BOOKING_STATUS_TRANSITIONS[current]:
        raise ConflictError("Invalid booking status transition")


def validate_terminal_status_note(status: str, note: str | None) -> None:
    if status in {BookingStatus.CANCELLED.value, BookingStatus.REJECTED.value}:
        if not (note and note.strip()):
            raise ConflictError(
                "note is required when cancelling or rejecting a booking"
            )

