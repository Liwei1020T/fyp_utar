from __future__ import annotations

from typing import Any
from typing import Protocol

from app.domain.recommendation.entities import RecommendationRunRecord
from app.shared.pagination import Page


class RecommendationRunRepository(Protocol):
    def create_run(
        self,
        *,
        run_id: str,
        user_id: str | None,
        request_payload: dict[str, Any],
        profile_payload: dict[str, Any],
        result_payloads: list[dict[str, Any]],
        algorithm_version: str,
    ) -> None: ...

    def list_runs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationRunRecord]: ...

    def get_run(self, run_id: str) -> RecommendationRunRecord | None: ...
