from __future__ import annotations

from typing import Protocol

from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import UserPreferenceVectorEntry


class RecommendationRepository(Protocol):
    def list_active_candidates(self) -> list[RecommendationCandidateModel]: ...

    def replace_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str,
        entries: list[dict[str, float | str | None]],
    ) -> list[UserPreferenceVectorEntry]: ...

    def list_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str | None = None,
    ) -> list[UserPreferenceVectorEntry]: ...

    def replace_score_cache(
        self,
        *,
        user_id: str,
        algorithm_version: str,
        results: list[dict[str, object]],
    ) -> list[CachedRecommendationRecord]: ...

    def clear_score_cache(self, *, user_id: str) -> None: ...

    def get_cached_results(
        self,
        *,
        user_id: str,
        algorithm_version: str | None = None,
    ) -> list[CachedRecommendationRecord]: ...

    def get_cached_result_detail(
        self,
        *,
        user_id: str,
        catalog_id: str,
        algorithm_version: str | None = None,
    ) -> CachedRecommendationRecord | None: ...
