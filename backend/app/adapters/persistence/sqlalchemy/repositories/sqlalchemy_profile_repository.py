from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.repositories.mappers import to_profile
from app.domain.profile.entities import PlayerProfile


class SqlAlchemyProfileRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: str) -> PlayerProfile | None:
        profile = self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        ).scalar_one_or_none()
        return to_profile(profile) if profile else None

    def upsert(self, profile: PlayerProfile) -> PlayerProfile:
        record = self.db.execute(
            select(Profile).where(Profile.user_id == profile.user_id)
        ).scalar_one_or_none()
        values = {
            "skill_level": profile.skill_level,
            "playing_style": profile.playing_style,
            "budget_min": profile.budget_min,
            "budget_max": profile.budget_max,
            "preferred_tension": profile.preferred_tension,
            "game_type": profile.game_type,
            "frequency_per_week": profile.frequency_per_week,
            "pref_attack": profile.pref_attack,
            "pref_comfort": profile.pref_comfort,
            "pref_control": profile.pref_control,
            "pref_durability": profile.pref_durability,
            "pref_elasticity": profile.pref_elasticity,
            "pref_sound": profile.pref_sound,
            "pref_string_movement": profile.pref_string_movement,
            "pref_tension_retention": profile.pref_tension_retention,
            "pref_value_for_money": profile.pref_value_for_money,
        }
        if record is None:
            record = Profile(user_id=profile.user_id, **values)
            self.db.add(record)
        else:
            for field, value in values.items():
                setattr(record, field, value)
        self.db.commit()
        self.db.refresh(record)
        return to_profile(record)
