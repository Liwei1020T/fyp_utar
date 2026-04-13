from __future__ import annotations

import json

from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

from app.adapters.persistence.sqlalchemy.models import RecommendationLog
from app.adapters.persistence.sqlalchemy.models import User
from app.adapters.persistence.sqlalchemy.repositories.mappers import (
    to_recommendation_log,
)
from app.domain.recommendation.entities import RecommendationLogRecord
from app.shared.pagination import Page


class SqlAlchemyRecommendationLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_log(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, object],
        response_payload: dict[str, object],
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
        self.db.commit()

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
