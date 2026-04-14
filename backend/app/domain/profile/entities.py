from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


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


@dataclass(frozen=True)
class PlayerProfile:
    user_id: str
    skill_level: str | None
    playing_style: str | None
    budget_tier: str | None
    budget_min: float | None
    budget_max: float | None
    preferred_tension: float | None
    game_type: str | None
    frequency_per_week: int | None
    preferred_feel: str | None
    recent_goal: str | None
    pref_attack: int | None
    pref_comfort: int | None
    pref_control: int | None
    pref_durability: int | None
    pref_elasticity: int | None
    pref_sound: int | None
    pref_string_movement: int | None
    pref_tension_retention: int | None
    pref_value_for_money: int | None
    created_at: datetime | None
    updated_at: datetime | None
