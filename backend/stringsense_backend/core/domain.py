from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    VENDOR = "vendor"


class AuthProvider(StrEnum):
    LOCAL = "local"
    FIREBASE_FUTURE_READY = "firebase_future_ready"


class SkillLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class PlayingStyle(StrEnum):
    ATTACKING = "attacking"
    BALANCED = "balanced"
    CONTROL_DEFENSIVE = "control_defensive"


class GameType(StrEnum):
    SINGLES = "singles"
    DOUBLES = "doubles"


class BookingStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    READY_FOR_PICKUP = "ready_for_pickup"
    PICKED_UP = "picked_up"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


USER_ROLES = tuple(role.value for role in UserRole)
SKILL_LEVELS = tuple(level.value for level in SkillLevel)
PLAYING_STYLES = tuple(style.value for style in PlayingStyle)
GAME_TYPES = tuple(game_type.value for game_type in GameType)
BOOKING_STATUSES = tuple(status.value for status in BookingStatus)

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
