from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.models import RecommendationLog
from app.adapters.persistence.sqlalchemy.models import RecommendationRun
from app.adapters.persistence.sqlalchemy.models import RecommendationRunItem
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_recommendation_log,
)
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_recommendation_run,
)
from app.domain.recommendation.entities import RecommendationLogRecord
from app.domain.recommendation.entities import RecommendationRunRecord
from app.shared.pagination import Page


class SqlAlchemyRecommendationLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        algorithm_version: str,
    ) -> None:
        self.db.add(
            RecommendationLog(
                user_id=user_id,
                request_json=json.dumps(
                    request_payload, ensure_ascii=False, sort_keys=True
                ),
                recommendation_json=json.dumps(response_payload, ensure_ascii=False),
                algorithm_version=algorithm_version,
            )
        )
        self.db.flush()

    def create_run(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, Any],
        profile_payload: dict[str, Any],
        result_payloads: list[dict[str, Any]],
        algorithm_version: str,
        matrix_version: str | None,
        feature_source_version: str | None,
    ) -> None:
        run = RecommendationRun(
            user_id=user_id,
            algorithm_version=algorithm_version,
            matrix_version=matrix_version,
            feature_source_version=feature_source_version,
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
                    budget_fit_score=_float(breakdown.get("budget_fit")),
                    confidence_score=_float(breakdown.get("confidence_score")),
                    nlp_review_score=_float(breakdown.get("nlp_review_score")),
                    score_breakdown=breakdown,
                    rationale=rationale,
                )
            )
        self.db.flush()

    def list_logs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationLogRecord]:
        query = select(RecommendationLog).options(joinedload(RecommendationLog.user))
        count_query = select(func.count()).select_from(RecommendationLog)

        if algorithm_version:
            version_filter = RecommendationLog.algorithm_version == algorithm_version
            query = query.where(version_filter)
            count_query = count_query.where(version_filter)
        if phone_number:
            phone_filter = User.phone_number.ilike(f"%{phone_number}%")
            query = query.join(RecommendationLog.user).where(phone_filter)
            count_query = count_query.join(RecommendationLog.user).where(phone_filter)

        total = self.db.execute(count_query).scalar_one()
        query = query.order_by(RecommendationLog.created_at.desc())
        if limit is not None:
            query = query.limit(limit).offset(offset)
        items = self.db.execute(query).unique().scalars().all()
        return Page(
            items=[to_recommendation_log(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )

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
