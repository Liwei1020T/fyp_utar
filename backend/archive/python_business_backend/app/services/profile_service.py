from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import CustomerProfile
from app.db.session import create_all_tables
from app.db.session import SessionLocal
from app.schemas.profile import ProfilePayload


class ProfileService:
    def reset(self) -> None:
        create_all_tables()
        with SessionLocal() as db:
            db.execute(delete(CustomerProfile))
            db.commit()

    def get(self, db: Session, user_id: str) -> dict | None:
        profile = db.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        ).scalar_one_or_none()
        if profile is None:
            return None
        return self._serialize_profile(profile)

    def save(self, db: Session, user_id: str, payload: ProfilePayload) -> dict:
        profile = db.execute(
            select(CustomerProfile).where(CustomerProfile.user_id == user_id)
        ).scalar_one_or_none()
        if profile is None:
            profile = CustomerProfile(user_id=user_id)
            db.add(profile)

        data = self._profile_updates_from_payload(payload)
        for field, value in data.items():
            setattr(profile, field, value)

        db.commit()
        db.refresh(profile)
        return self._serialize_profile(profile)

    @staticmethod
    def _serialize_profile(profile: CustomerProfile) -> dict:
        budget = ProfileService._serialize_budget(profile)
        data = {
            "skill_level": profile.skill_level,
            "playing_style": profile.playing_style,
            "budget": budget,
            "preferred_tension": ProfileService._decimal_to_float(
                profile.preferred_tension
            ),
            "durability_priority": profile.durability_priority,
            "repulsion_priority": profile.repulsion_priority,
            "control_priority": profile.control_priority,
            "sound_priority": profile.sound_priority,
            "tension_retention_priority": profile.tension_retention_priority,
        }
        return {key: value for key, value in data.items() if value is not None}

    @staticmethod
    def _decimal_to_float(value: Decimal | None) -> float | None:
        if value is None:
            return None
        return float(value)

    @staticmethod
    def _serialize_budget(profile: CustomerProfile) -> dict[str, float] | None:
        budget_min = ProfileService._decimal_to_float(profile.budget_min)
        budget_max = ProfileService._decimal_to_float(profile.budget_max)
        if budget_min is None and budget_max is None:
            return None
        budget: dict[str, float] = {}
        if budget_min is not None:
            budget["min"] = budget_min
        if budget_max is not None:
            budget["max"] = budget_max
        return budget

    @staticmethod
    def _profile_updates_from_payload(payload: ProfilePayload) -> dict:
        data = payload.model_dump(exclude_none=True)
        budget = data.pop("budget", None)
        if budget is not None:
            data["budget_min"] = budget.get("min")
            data["budget_max"] = budget.get("max")
        return data


profile_service = ProfileService()
