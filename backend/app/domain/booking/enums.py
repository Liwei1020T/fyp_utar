from __future__ import annotations

from enum import StrEnum


class BookingStatus(StrEnum):
    AWAITING_DROPOFF = "awaiting_dropoff"
    IN_PROGRESS = "in_progress"
    READY_FOR_COLLECTION = "ready_for_collection"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"

