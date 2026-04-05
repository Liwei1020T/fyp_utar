from __future__ import annotations

from ai_service.schemas import RagQueryRequest
from ai_service.service import RecommendationService


class RagAdapter:
    def __init__(self) -> None:
        self.service = RecommendationService()

    def query(self, query: str, top_k: int) -> dict[str, object]:
        response = self.service.rag_query(RagQueryRequest(query=query, top_k=top_k))
        return response.model_dump(mode="json")
