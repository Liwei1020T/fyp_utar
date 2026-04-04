from __future__ import annotations

from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from stringsense_backend.api.dependencies import CurrentUser
from stringsense_backend.api.dependencies import get_current_customer
from stringsense_backend.core.errors import NotFoundError
from stringsense_backend.core.serialization import decimal_to_float
from stringsense_backend.core.serialization import isoformat_or_none
from stringsense_backend.db.models import Profile
from stringsense_backend.db.session import get_db


router = APIRouter(prefix="/profile", tags=["profile"])


class ProfilePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    skill_level: str | None = Field(
        default=None, pattern="^(beginner|intermediate|advanced)$"
    )
    playing_style: str | None = Field(
        default=None,
        pattern="^(attacking|balanced|control_defensive)$",
    )
    budget_min: float | None = Field(default=None, ge=0, le=999)
    budget_max: float | None = Field(default=None, ge=0, le=999)
    preferred_tension: float | None = Field(default=None, ge=16, le=35)
    game_type: str | None = Field(default=None, pattern="^(singles|doubles)$")
    frequency_per_week: int | None = Field(default=None, ge=0, le=14)
    pref_attack: int | None = Field(default=None, ge=1, le=5)
    pref_comfort: int | None = Field(default=None, ge=1, le=5)
    pref_control: int | None = Field(default=None, ge=1, le=5)
    pref_durability: int | None = Field(default=None, ge=1, le=5)
    pref_elasticity: int | None = Field(default=None, ge=1, le=5)
    pref_sound: int | None = Field(default=None, ge=1, le=5)
    pref_string_movement: int | None = Field(default=None, ge=1, le=5)
    pref_tension_retention: int | None = Field(default=None, ge=1, le=5)
    pref_value_for_money: int | None = Field(default=None, ge=1, le=5)

    @model_validator(mode="after")
    def validate_budget(self) -> "ProfilePayload":
        if (
            self.budget_min is not None
            and self.budget_max is not None
            and self.budget_min > self.budget_max
        ):
            raise ValueError("budget_min must be less than or equal to budget_max")
        return self


class ProfileOut(ProfilePayload):
    created_at: str | None = None
    updated_at: str | None = None


def serialize_profile(profile: Profile) -> ProfileOut:
    return ProfileOut(
        skill_level=profile.skill_level,
        playing_style=profile.playing_style,
        budget_min=decimal_to_float(profile.budget_min),
        budget_max=decimal_to_float(profile.budget_max),
        preferred_tension=decimal_to_float(profile.preferred_tension),
        game_type=profile.game_type,
        frequency_per_week=profile.frequency_per_week,
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


def get_profile_or_none(db: Session, user_id: str) -> Profile | None:
    return db.execute(
        select(Profile).where(Profile.user_id == user_id)
    ).scalar_one_or_none()


@router.get("", response_model=ProfileOut)
def get_profile(
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = get_profile_or_none(db, current_user.user_id)
    if profile is None:
        raise NotFoundError("Profile not found")
    return serialize_profile(profile)


@router.put("", response_model=ProfileOut)
def upsert_profile(
    payload: ProfilePayload,
    current_user: CurrentUser = Depends(get_current_customer),
    db: Session = Depends(get_db),
) -> ProfileOut:
    profile = get_profile_or_none(db, current_user.user_id)
    data = payload.model_dump()
    if profile is None:
        profile = Profile(user_id=current_user.user_id, **data)
        db.add(profile)
    else:
        for field, value in data.items():
            setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return serialize_profile(profile)
