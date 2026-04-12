from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.domain.recommendation.entities import RecommendationLogRecord
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.shared.serialization import isoformat_or_none


class RecommendationRequestDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    skill_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    playing_style: str = Field(pattern="^(attacking|balanced|control_defensive)$")
    budget_min: float = Field(ge=0, le=999)
    budget_max: float = Field(ge=0, le=999)
    preferred_tension: float = Field(ge=16, le=35)
    game_type: str = Field(pattern="^(singles|doubles)$")
    frequency_per_week: int = Field(ge=0, le=14)
    pref_attack: int = Field(ge=1, le=5)
    pref_comfort: int = Field(ge=1, le=5)
    pref_control: int = Field(ge=1, le=5)
    pref_durability: int = Field(ge=1, le=5)
    pref_elasticity: int = Field(ge=1, le=5)
    pref_sound: int = Field(ge=1, le=5)
    pref_string_movement: int = Field(ge=1, le=5)
    pref_tension_retention: int = Field(ge=1, le=5)
    pref_value_for_money: int = Field(ge=1, le=5)
    top_n: int = Field(default=5, ge=1, le=10)

    @model_validator(mode="after")
    def validate_budget(self) -> "RecommendationRequestDto":
        if self.budget_min > self.budget_max:
            raise ValueError("budget_min must be less than or equal to budget_max")
        return self


class RecommendationResultDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rank: int
    catalog_id: str | None = None
    string_name: str
    brand: str
    model_name: str | None = None
    score: float
    price_rm: float | None
    aspect_scores: dict[str, float]
    reasons: list[str]
    score_breakdown: dict[str, float] | None = None
    rationale_payload: dict[str, Any] | None = None
    generated_at: str | None = None


class RecommendationResponseDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    results: list[RecommendationResultDto]
    generated_at: str | None = None


class RecommendationDetailDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    result: RecommendationResultDto
    generated_at: str | None = None


class ProfileRecommendationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    top_n: int = Field(default=5, ge=1, le=10)


def recommendation_request_to_domain(
    payload: RecommendationRequestDto,
) -> RecommendationRequestModel:
    return RecommendationRequestModel(**payload.model_dump())


def recommendation_response_to_dto(
    response: RecommendationResponseModel,
) -> RecommendationResponseDto:
    return RecommendationResponseDto(
        algorithm_version=response.algorithm_version,
        results=[recommendation_result_to_dto(item) for item in response.results],
        generated_at=isoformat_or_none(response.generated_at),
    )


def recommendation_result_to_dto(
    item: RecommendationResultModel,
) -> RecommendationResultDto:
    return RecommendationResultDto(
        rank=item.rank,
        catalog_id=item.catalog_id,
        string_name=item.string_name,
        brand=item.brand,
        model_name=item.model_name,
        score=item.score,
        price_rm=item.price_rm,
        aspect_scores=item.aspect_scores,
        reasons=item.reasons,
        score_breakdown=item.score_breakdown,
        rationale_payload=item.rationale_payload,
        generated_at=isoformat_or_none(item.generated_at),
    )


def recommendation_detail_to_dto(
    *,
    algorithm_version: str,
    result: RecommendationResultModel,
    generated_at: datetime | None = None,
) -> RecommendationDetailDto:
    return RecommendationDetailDto(
        algorithm_version=algorithm_version,
        result=recommendation_result_to_dto(result),
        generated_at=isoformat_or_none(generated_at or result.generated_at),
    )


def recommendation_log_to_dict(item: RecommendationLogRecord) -> dict[str, Any]:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "phone_number": item.phone_number,
        "username": item.username,
        "request": item.request,
        "recommendation": item.recommendation,
        "algorithm_version": item.algorithm_version,
        "created_at": isoformat_or_none(item.created_at),
    }
