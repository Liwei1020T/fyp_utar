from __future__ import annotations

from app.adapters.services.ai.recommendation_engine_adapter import (
    RecommendationEngineAdapter,
)

ai_service = RecommendationEngineAdapter()

__all__ = ["ai_service"]
