from __future__ import annotations

from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"


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
    AWAITING_DROPOFF = "awaiting_dropoff"
    IN_PROGRESS = "in_progress"
    READY_FOR_COLLECTION = "ready_for_collection"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


USER_ROLES = tuple(role.value for role in UserRole)
SKILL_LEVELS = tuple(level.value for level in SkillLevel)
PLAYING_STYLES = tuple(style.value for style in PlayingStyle)
GAME_TYPES = tuple(game_type.value for game_type in GameType)
BOOKING_STATUSES = tuple(status.value for status in BookingStatus)

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
    BookingStatus.READY_FOR_COLLECTION: {
        BookingStatus.COMPLETED,
    },
    BookingStatus.COMPLETED: set(),
    BookingStatus.CANCELLED: set(),
    BookingStatus.REJECTED: set(),
}
