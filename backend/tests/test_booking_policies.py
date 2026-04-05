from __future__ import annotations

import pytest

from app.domain.booking.enums import BookingStatus
from app.domain.booking.policies import validate_status_transition
from app.shared.errors import ConflictError


def test_booking_status_transition_accepts_valid_progression() -> None:
    validate_status_transition(
        BookingStatus.AWAITING_DROPOFF.value,
        BookingStatus.IN_PROGRESS.value,
    )
    validate_status_transition(
        BookingStatus.IN_PROGRESS.value,
        BookingStatus.READY_FOR_COLLECTION.value,
    )
    validate_status_transition(
        BookingStatus.READY_FOR_COLLECTION.value,
        BookingStatus.COMPLETED.value,
    )


def test_booking_status_transition_rejects_invalid_progression() -> None:
    with pytest.raises(ConflictError, match="Invalid booking status transition"):
        validate_status_transition(
            BookingStatus.AWAITING_DROPOFF.value,
            BookingStatus.COMPLETED.value,
        )

