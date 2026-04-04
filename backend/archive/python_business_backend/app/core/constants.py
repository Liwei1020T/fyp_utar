from __future__ import annotations

from decimal import Decimal
from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlayingStyle(StrEnum):
    ATTACKING = "attacking"
    BALANCED = "balanced"
    CONTROL = "control"
    DEFENSIVE = "defensive"


class PlayFrequency(StrEnum):
    LOW = "low"
    WEEKLY = "weekly"
    HIGH = "high"


class PreferredFeel(StrEnum):
    SOFT = "soft"
    MEDIUM = "medium"
    HARD = "hard"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


BOOKING_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {
        BookingStatus.CONFIRMED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.CONFIRMED: {
        BookingStatus.IN_PROGRESS,
        BookingStatus.CANCELLED,
    },
    BookingStatus.IN_PROGRESS: {
        BookingStatus.READY_FOR_PICKUP,
        BookingStatus.CANCELLED,
    },
    BookingStatus.READY_FOR_PICKUP: {
        BookingStatus.PICKED_UP,
        BookingStatus.CANCELLED,
    },
    BookingStatus.PICKED_UP: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.REJECTED: set(),
}


PRIORITY_MIN = 1
PRIORITY_MAX = 5
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MIN_TENSION = Decimal("18.0")
MAX_TENSION = Decimal("35.0")
MAX_BUDGET = Decimal("500.0")
MAX_PRICE = Decimal("500.0")
MAX_OPTIONAL_NOTE_LENGTH = 500
MAX_DESCRIPTION_LENGTH = 1000
MAX_PROFILE_NOTE_LENGTH = 500
PASSWORD_RESET_CODE_LENGTH = 6
