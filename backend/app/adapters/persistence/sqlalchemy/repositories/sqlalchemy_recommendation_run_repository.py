from __future__ import annotations

from typing import Any

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.models import RecommendationRun
from app.adapters.persistence.sqlalchemy.models import RecommendationRunItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_recommendation_run,
)
from app.domain.recommendation.entities import RecommendationRunRecord
from app.shared.pagination import Page


class SqlAlchemyRecommendationRunRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_run(
        self,
        *,
        run_id: str,
        user_id: str | None,
        request_payload: dict[str, Any],
        profile_payload: dict[str, Any],
        result_payloads: list[dict[str, Any]],
        algorithm_version: str,
    ) -> None:
        run = RecommendationRun(
            id=run_id,
            user_id=user_id,
            algorithm_version=algorithm_version,
            request_snapshot=request_payload,
            profile_snapshot=profile_payload,
        )
        self.db.add(run)
        self.db.flush()
        for result in result_payloads:
            rationale = _mapping(result.get("rationale_payload"))
            breakdown = _mapping(result.get("score_breakdown"))
            self.db.add(
                RecommendationRunItem(
                    run_id=run.id,
                    catalog_id=str(result.get("catalog_id") or ""),
                    rank_position=int(result.get("rank") or 0),
                    final_score=_float(result.get("score")) or 0.0,
                    preference_match_score=_float(breakdown.get("preference_match")),
                    rule_fit_score=_float(breakdown.get("rule_fit")),
                    value_for_money_score=_float(breakdown.get("value_for_money")),
                    nlp_review_score=_float(breakdown.get("nlp_review_score")),
                    score_breakdown=breakdown,
                    rationale=rationale,
                )
            )
        self.db.flush()

    def list_runs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationRunRecord]:
        query = select(RecommendationRun).options(
            joinedload(RecommendationRun.user),
            selectinload(RecommendationRun.items),
        )
        count_query = select(func.count()).select_from(RecommendationRun)

        if algorithm_version:
            version_filter = RecommendationRun.algorithm_version == algorithm_version
            query = query.where(version_filter)
            count_query = count_query.where(version_filter)
        if phone_number:
            phone_filter = User.phone_number.ilike(f"%{phone_number}%")
            query = query.join(RecommendationRun.user).where(phone_filter)
            count_query = count_query.join(RecommendationRun.user).where(phone_filter)

        total = self.db.execute(count_query).scalar_one()
        query = query.order_by(RecommendationRun.generated_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).unique().scalars().all()
        return Page(
            items=[to_recommendation_run(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

    def get_run(self, run_id: str) -> RecommendationRunRecord | None:
        item = (
            self.db.execute(
                select(RecommendationRun)
                .options(
                    joinedload(RecommendationRun.user),
                    selectinload(RecommendationRun.items),
                )
                .where(RecommendationRun.id == run_id)
            )
            .unique()
            .scalar_one_or_none()
        )
        return to_recommendation_run(item) if item else None


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _float(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value).__name__}")
