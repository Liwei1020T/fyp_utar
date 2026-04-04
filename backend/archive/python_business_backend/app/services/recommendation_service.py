import json
from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_service.schemas.recommendation import RecommendRequest
from ai_service.schemas.recommendation import RecommendationContext
from ai_service.schemas.recommendation import StringCandidate
from ai_service.services.recommendation_engine import generate_recommendations
from app.db.models import AppUser
from app.db.models import RecommendationLog
from app.db.session import create_all_tables
from app.db.session import SessionLocal
from app.schemas.recommendation import RecommendationPayload
from app.services.string_service import string_service


class RecommendationService:
    def reset(self) -> None:
        create_all_tables()
        with SessionLocal() as db:
            db.execute(delete(RecommendationLog))
            db.commit()

    def logs(
        self,
        db: Session,
        *,
        phone_number: str | None = None,
        algorithm_version: str | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        query = select(RecommendationLog).join(
            AppUser, AppUser.id == RecommendationLog.customer_user_id
        )
        count_query = (
            select(func.count())
            .select_from(RecommendationLog)
            .join(AppUser, AppUser.id == RecommendationLog.customer_user_id)
        )

        if phone_number:
            query = query.where(AppUser.phone_number.ilike(f"%{phone_number.strip()}%"))
            count_query = count_query.where(
                AppUser.phone_number.ilike(f"%{phone_number.strip()}%")
            )

        if algorithm_version:
            query = query.where(
                RecommendationLog.algorithm_version == algorithm_version
            )
            count_query = count_query.where(
                RecommendationLog.algorithm_version == algorithm_version
            )

        total = db.execute(count_query).scalar_one()
        query = query.order_by(RecommendationLog.created_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)

        logs = db.execute(query).scalars().all()
        return [self._serialize_log(db, item) for item in logs], total

    def generate(
        self, db: Session, *, user_id: str, payload: RecommendationPayload
    ) -> dict:
        strings, _ = string_service.list_active(db)
        ai_response = generate_recommendations(
            RecommendRequest(
                profile=RecommendationContext(user_id=user_id),
                request=RecommendationContext(
                    user_id=user_id,
                    skill_level=payload.skill_level,
                    playing_style=payload.playing_style,
                    budget=payload.budget.model_dump()
                    if payload.budget is not None
                    else None,
                    preferred_tension=float(payload.preferred_tension)
                    if payload.preferred_tension is not None
                    else None,
                    durability_priority=payload.durability_priority,
                    repulsion_priority=payload.repulsion_priority,
                    control_priority=payload.control_priority,
                    sound_priority=payload.sound_priority,
                    tension_retention_priority=payload.tension_retention_priority,
                ),
                catalog=[StringCandidate(**item) for item in strings],
                top_k=5,
            )
        )
        results = [item.model_dump() for item in ai_response.results]
        algorithm_version = ai_response.algorithm_version
        db.add(
            RecommendationLog(
                customer_user_id=user_id,
                input_snapshot=json.dumps(
                    self._json_ready(payload.model_dump(exclude_none=True))
                ),
                result_snapshot=json.dumps(results),
                algorithm_version=algorithm_version,
            )
        )
        db.commit()

        return {
            "results": results,
            "algorithm_version": algorithm_version,
        }

    def _json_ready(self, value):
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, dict):
            return {key: self._json_ready(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_ready(item) for item in value]
        return value

    def _serialize_log(self, db: Session, log: RecommendationLog) -> dict:
        user = db.execute(
            select(AppUser).where(AppUser.id == log.customer_user_id)
        ).scalar_one_or_none()
        return {
            "user_id": log.customer_user_id,
            "phone_number": user.phone_number if user is not None else None,
            "input_snapshot": json.loads(log.input_snapshot),
            "result_snapshot": json.loads(log.result_snapshot),
            "algorithm_version": log.algorithm_version,
            "created_at": log.created_at.isoformat()
            if log.created_at is not None
            else None,
        }


recommendation_service = RecommendationService()
