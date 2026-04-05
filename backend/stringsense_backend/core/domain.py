from __future__ import annotations

from app.domain.auth.entities import AuthProvider
from app.domain.auth.entities import UserRole
from app.domain.booking.enums import BookingStatus
from app.domain.booking.policies import BOOKING_STATUS_TRANSITIONS
from app.domain.profile.entities import GameType
from app.domain.profile.entities import PlayingStyle
from app.domain.profile.entities import SkillLevel

USER_ROLES = tuple(role.value for role in UserRole)
SKILL_LEVELS = tuple(level.value for level in SkillLevel)
PLAYING_STYLES = tuple(style.value for style in PlayingStyle)
GAME_TYPES = tuple(game_type.value for game_type in GameType)
BOOKING_STATUSES = tuple(status.value for status in BookingStatus)

__all__ = [
    "AuthProvider",
    "BOOKING_STATUSES",
    "BOOKING_STATUS_TRANSITIONS",
    "BookingStatus",
    "GAME_TYPES",
    "GameType",
    "PLAYING_STYLES",
    "PlayingStyle",
    "SKILL_LEVELS",
    "SkillLevel",
    "USER_ROLES",
    "UserRole",
]
