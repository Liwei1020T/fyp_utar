from __future__ import annotations

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Header
from fastapi import HTTPException
from fastapi import status

from ai_service.core.config import get_ai_settings
from ai_service.schemas import ExplainRequest
from ai_service.schemas import ExplainResponse
from ai_service.schemas import RagQueryRequest
from ai_service.schemas import RagQueryResponse
from ai_service.schemas import RecommendationRequest
from ai_service.schemas import RecommendationResponse
from ai_service.schemas import ReviewAnalyzeRequest
from ai_service.schemas import ReviewAnalyzeResponse
from ai_service.service import RecommendationService


def _verify_internal_api_key(
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    expected = get_ai_settings().internal_api_key
    if x_internal_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )


service = RecommendationService()
app = FastAPI(title=get_ai_settings().app_name)


@app.get("/health")
def health_check() -> dict[str, object]:
    return service.health()


@app.get(
    "/internal/ai/strings",
    dependencies=[Depends(_verify_internal_api_key)],
)
def list_strings() -> list[dict[str, object]]:
    return service.list_strings()


@app.get(
    "/internal/ai/strings/{string_name}",
    dependencies=[Depends(_verify_internal_api_key)],
)
def get_string(string_name: str) -> dict[str, object]:
    try:
        return service.get_string(string_name)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="String not found") from exc


@app.post(
    "/internal/ai/recommend",
    response_model=RecommendationResponse,
    dependencies=[Depends(_verify_internal_api_key)],
)
def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    return service.recommend(payload)


@app.post(
    "/internal/ai/explain",
    response_model=ExplainResponse,
    dependencies=[Depends(_verify_internal_api_key)],
)
def explain(payload: ExplainRequest) -> ExplainResponse:
    return service.explain(payload)


@app.post(
    "/internal/ai/reviews/analyze",
    response_model=ReviewAnalyzeResponse,
    dependencies=[Depends(_verify_internal_api_key)],
)
def review_analyze(payload: ReviewAnalyzeRequest) -> ReviewAnalyzeResponse:
    return service.analyze_reviews(payload)


@app.post(
    "/internal/ai/rag/query",
    response_model=RagQueryResponse,
    dependencies=[Depends(_verify_internal_api_key)],
)
def rag_query(payload: RagQueryRequest) -> RagQueryResponse:
    return service.rag_query(payload)
