from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from app.domain.recommendation.entities import RecommendationLogRecord
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
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
    string_name: str
    brand: str
    score: float
    price_rm: float | None
    aspect_scores: dict[str, float]
    reasons: list[str]


class RecommendationResponseDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    algorithm_version: str
    results: list[RecommendationResultDto]


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
        results=[
            RecommendationResultDto(
                rank=item.rank,
                string_name=item.string_name,
                brand=item.brand,
                score=item.score,
                price_rm=item.price_rm,
                aspect_scores=item.aspect_scores,
                reasons=item.reasons,
            )
            for item in response.results
        ],
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
