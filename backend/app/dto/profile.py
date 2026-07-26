from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.domain.profile.entities import PlayerProfile
from app.shared.serialization import isoformat_or_none


class ProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str | None = Field(default=None, min_length=2, max_length=64)
    skill_level: str | None = Field(
        default=None,
        pattern="^(beginner|intermediate|advanced)$",
    )
    playing_style: str | None = Field(
        default=None,
        pattern="^(attacking|balanced|control_defensive)$",
    )
    budget_tier: str | None = Field(
        default=None,
        pattern="^(below_30|between_30_50|above_50)$",
    )
    preferred_tension: float | None = Field(default=None, ge=16, le=35)
    game_type: str | None = Field(default=None, pattern="^(singles|doubles)$")
    frequency_per_week: int | None = Field(default=None, ge=0, le=14)
    preferred_feel: str | None = Field(
        default=None,
        pattern="^(soft|balanced|crisp|hard)$",
    )
    recent_goal: str | None = Field(default=None, max_length=500)
    pref_attack: int | None = Field(default=None, ge=1, le=10)
    pref_comfort: int | None = Field(default=None, ge=1, le=10)
    pref_control: int | None = Field(default=None, ge=1, le=10)
    pref_durability: int | None = Field(default=None, ge=1, le=10)
    pref_elasticity: int | None = Field(default=None, ge=1, le=10)
    pref_sound: int | None = Field(default=None, ge=1, le=10)
    pref_string_movement: int | None = Field(default=None, ge=1, le=10)
    pref_tension_retention: int | None = Field(default=None, ge=1, le=10)
    pref_value_for_money: int | None = Field(default=None, ge=1, le=10)


class ProfileOut(ProfilePayload):
    username: str
    created_at: str | None = None
    updated_at: str | None = None


class PrivacySettingsPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    analytics_consent: bool = True
    personalization_consent: bool = True
    marketing_consent: bool = False


def profile_to_dto(profile: PlayerProfile, *, username: str) -> ProfileOut:
    return ProfileOut(
        username=username,
        skill_level=profile.skill_level,
        playing_style=profile.playing_style,
        budget_tier=profile.budget_tier,
        preferred_tension=profile.preferred_tension,
        game_type=profile.game_type,
        frequency_per_week=profile.frequency_per_week,
        preferred_feel=profile.preferred_feel,
        recent_goal=profile.recent_goal,
        pref_attack=profile.pref_attack,
        pref_comfort=profile.pref_comfort,
        pref_control=profile.pref_control,
        pref_durability=profile.pref_durability,
        pref_elasticity=profile.pref_elasticity,
        pref_sound=profile.pref_sound,
        pref_string_movement=profile.pref_string_movement,
        pref_tension_retention=profile.pref_tension_retention,
        pref_value_for_money=profile.pref_value_for_money,
        created_at=isoformat_or_none(profile.created_at),
        updated_at=isoformat_or_none(profile.updated_at),
    )
