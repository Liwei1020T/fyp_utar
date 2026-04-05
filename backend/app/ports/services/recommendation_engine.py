from __future__ import annotations

from typing import Protocol
from typing import Sequence

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel


class RecommendationEngine(Protocol):
    def recommend(
        self,
        catalog: Sequence[StringItem],
        request: RecommendationRequestModel,
    ) -> RecommendationResponseModel: ...

