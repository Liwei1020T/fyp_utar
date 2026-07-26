from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.persistence.sqlalchemy.models import Profile
from app.adapters.persistence.sqlalchemy.models import User
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

    def upsert(
        self,
        profile: PlayerProfile,
        *,
        username: str | None = None,
    ) -> PlayerProfile:
        user = self.db.get(User, profile.user_id)
        assert user is not None
        if username is not None:
            user.username = username.strip()

        record = self.db.execute(
            select(Profile).where(Profile.user_id == profile.user_id)
        ).scalar_one_or_none()
        values = {
            "skill_level": profile.skill_level,
            "playing_style": profile.playing_style,
            "budget_tier": profile.budget_tier,
            "preferred_tension": profile.preferred_tension,
            "game_type": profile.game_type,
            "frequency_per_week": profile.frequency_per_week,
            "preferred_feel": profile.preferred_feel,
            "recent_goal": profile.recent_goal,
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

    def get_notification_preferences(self, user_id: str) -> dict[str, bool]:
        record = self._get_or_create_profile(user_id)
        return dict(record.notification_preferences or {})

    def update_notification_preferences(
        self,
        user_id: str,
        preferences: dict[str, bool],
    ) -> dict[str, bool]:
        record = self._get_or_create_profile(user_id)
        record.notification_preferences = dict(preferences)
        self.db.commit()
        return dict(record.notification_preferences)

    def get_privacy_settings(self, user_id: str) -> dict[str, bool]:
        record = self._get_or_create_profile(user_id)
        return dict(record.privacy_settings or {})

    def update_privacy_settings(
        self,
        user_id: str,
        settings: dict[str, bool],
    ) -> dict[str, bool]:
        record = self._get_or_create_profile(user_id)
        record.privacy_settings = dict(settings)
        self.db.commit()
        return dict(record.privacy_settings)

    def _get_or_create_profile(self, user_id: str) -> Profile:
        record = self.db.execute(
            select(Profile).where(Profile.user_id == user_id)
        ).scalar_one_or_none()
        if record is None:
            record = Profile(user_id=user_id, notification_preferences={})
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        return record
