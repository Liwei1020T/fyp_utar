from __future__ import annotations

from dataclasses import dataclass

from app.domain.recommendation.entities import RecommendationRunRecord
from app.ports.repositories.recommendation_run_repository import (
    RecommendationRunRepository,
)
from app.shared.errors import NotFoundError


@dataclass
class GetRecommendationRunUseCase:
    recommendation_run_repository: RecommendationRunRepository

    def execute(self, run_id: str) -> RecommendationRunRecord:
        run = self.recommendation_run_repository.get_run(run_id)
        if run is None:
            raise NotFoundError("Recommendation run not found")
        return run
