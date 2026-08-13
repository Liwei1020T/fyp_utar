from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from app.domain.recommendation.entities import RecommendationLogRecord
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.entities import RecommendationRunItemRecord
from app.domain.recommendation.entities import RecommendationRunRecord
from app.domain.recommendation.entities import CommunitySnapshot
from app.shared.serialization import isoformat_or_none


class RecommendationRequestDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    skill_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    playing_style: str = Field(pattern="^(attacking|balanced|control_defensive)$")
    preferred_tension: float = Field(ge=16, le=35)
    frequency_per_week: int = Field(ge=0, le=14)
    preferred_feel: str = Field(pattern="^(soft|medium|hard)$")
    preferred_gauge: str = Field(pattern="^(no_preference|thin|medium|thick)$")
    recent_goal: str = Field(
        pattern="^(balanced|power|control|durability|comfort|tension_retention|value_for_money)$"
    )
    pref_attack: int = Field(ge=1, le=10)
    pref_comfort: int = Field(ge=1, le=10)
    pref_control: int = Field(ge=1, le=10)
    pref_durability: int = Field(ge=1, le=10)
    pref_elasticity: int = Field(ge=1, le=10)
    pref_sound: int = Field(ge=1, le=10)
    pref_string_movement: int = Field(ge=1, le=10)
    pref_tension_retention: int = Field(ge=1, le=10)
    pref_value_for_money: int = Field(ge=1, le=10)
    top_n: int = Field(default=5, ge=1, le=10)


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
    racket_id: str | None = Field(default=None, min_length=1, max_length=36)


class RecommendationRunItemDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    catalog_id: str
    rank_position: int
    final_score: float
    preference_match_score: float | None = None
    rule_fit_score: float | None = None
    value_for_money_score: float | None = None
    nlp_review_score: float | None = None
    score_breakdown: dict[str, Any]
    rationale: dict[str, Any]


class RecommendationRunDto(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    user_id: str | None = None
    phone_number: str | None = None
    username: str | None = None
    algorithm_version: str
    request_snapshot: dict[str, Any]
    profile_snapshot: dict[str, Any]
    generated_at: str | None = None
    items: list[RecommendationRunItemDto]


def community_snapshot_to_dict(
    snapshot: CommunitySnapshot,
    *,
    racket_model_key: str | None,
) -> dict[str, object]:
    return {
        "policy_version": "community_feedback_v1",
        "snapshot_version": snapshot.snapshot_version,
        "racket_model_key": racket_model_key,
        "strings": [
            {
                "string_id": catalog_id,
                "features": {
                    feature: {
                        "score": aggregate.normalized_score,
                        "distinct_users": aggregate.distinct_users,
                        "booking_count": aggregate.booking_count,
                        "confidence": aggregate.confidence,
                        "weight": aggregate.weight,
                        "evidence_scope": aggregate.evidence_scope,
                        "source_version": aggregate.source_version,
                    }
                    for feature, aggregate in sorted(features.items())
                },
            }
            for catalog_id, features in sorted(snapshot.by_catalog.items())
        ],
    }


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


def recommendation_run_to_dict(item: RecommendationRunRecord) -> dict[str, Any]:
    return RecommendationRunDto(
        id=item.id,
        user_id=item.user_id,
        phone_number=item.phone_number,
        username=item.username,
        algorithm_version=item.algorithm_version,
        request_snapshot=item.request_snapshot,
        profile_snapshot=item.profile_snapshot,
        generated_at=isoformat_or_none(item.generated_at),
        items=[recommendation_run_item_to_dto(run_item) for run_item in item.items],
    ).model_dump()


def recommendation_run_item_to_dto(
    item: RecommendationRunItemRecord,
) -> RecommendationRunItemDto:
    return RecommendationRunItemDto(
        id=item.id,
        catalog_id=item.catalog_id,
        rank_position=item.rank_position,
        final_score=item.final_score,
        preference_match_score=item.preference_match_score,
        rule_fit_score=item.rule_fit_score,
        value_for_money_score=item.value_for_money_score,
        nlp_review_score=item.nlp_review_score,
        score_breakdown=item.score_breakdown,
        rationale=item.rationale,
    )
