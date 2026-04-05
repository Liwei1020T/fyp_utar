from __future__ import annotations

from dataclasses import dataclass

from app.domain.recommendation.entities import RecommendationLogRecord
from app.ports.repositories.recommendation_log_repository import (
    RecommendationLogRepository,
)
from app.shared.pagination import Page


@dataclass
class ListRecommendationLogsUseCase:
    recommendation_log_repository: RecommendationLogRepository

    def execute(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationLogRecord]:
        return self.recommendation_log_repository.list_logs(
            phone_number=phone_number,
            algorithm_version=algorithm_version,
            limit=limit,
            offset=offset,
        )
