from __future__ import annotations

from ai_service.schemas import ReviewAnalyzeRequest
from ai_service.service import RecommendationService


class ReviewAnalysisAdapter:
    def __init__(self) -> None:
        self.service = RecommendationService()

    def analyze_reviews(self, reviews: list[str]) -> dict[str, object]:
        response = self.service.analyze_reviews(ReviewAnalyzeRequest(reviews=reviews))
        return response.model_dump(mode="json")

