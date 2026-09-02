from __future__ import annotations

from dataclasses import dataclass

from app.domain.recommendation.entities import RecommendationRunRecord
from app.ports.repositories.recommendation_run_repository import (
    RecommendationRunRepository,
)
from app.shared.pagination import Page


@dataclass
class ListRecommendationRunsUseCase:
    recommendation_run_repository: RecommendationRunRepository

    def execute(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationRunRecord]:
        return self.recommendation_run_repository.list_runs(
            phone_number=phone_number,
            algorithm_version=algorithm_version,
            limit=limit,
            offset=offset,
        )
