from __future__ import annotations

from typing import Any
from typing import Protocol

from app.domain.recommendation.entities import RecommendationLogRecord
from app.shared.pagination import Page


class RecommendationLogRepository(Protocol):
    def create_log(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, Any],
        response_payload: dict[str, Any],
        algorithm_version: str,
    ) -> None: ...

    def list_logs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page[RecommendationLogRecord]: ...

