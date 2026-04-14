from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field

from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationDetailModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_log_repository import (
    RecommendationLogRepository,
)
from app.ports.repositories.recommendation_repository import RecommendationRepository
from app.shared.errors import BadRequestError
from app.shared.errors import NotFoundError


REQUIRED_PROFILE_FIELDS = {
    "skill_level",
    "playing_style",
    "budget_tier",
    "preferred_tension",
    "game_type",
    "frequency_per_week",
    "pref_attack",
    "pref_comfort",
    "pref_control",
    "pref_durability",
    "pref_elasticity",
    "pref_sound",
    "pref_string_movement",
    "pref_tension_retention",
    "pref_value_for_money",
}


@dataclass
class GenerateRecommendationUseCase:
    profile_repository: ProfileRepository
    recommendation_repository: RecommendationRepository
    recommendation_log_repository: RecommendationLogRepository
    scorer: Fyp1ContentRecommendationScorer = field(
        default_factory=Fyp1ContentRecommendationScorer
    )

    def execute_preview(
        self,
        *,
        user_id: str | None,
        request: RecommendationRequestModel,
    ) -> RecommendationResponseModel:
        return self._execute(
            user_id=user_id,
            request=request,
            persist=False,
        )

    def execute_profile(
        self,
        *,
        user_id: str,
        top_n: int,
    ) -> RecommendationResponseModel:
        profile = self.profile_repository.get_by_user_id(user_id)
        if profile is None:
            raise NotFoundError("Profile not found")

        missing_fields = [
            field_name
            for field_name, value in profile.__dict__.items()
            if field_name in REQUIRED_PROFILE_FIELDS and value is None
        ]
        if missing_fields:
            raise BadRequestError("Profile is incomplete for recommendation")

        request = RecommendationRequestModel(
            user_id=user_id,
            skill_level=profile.skill_level or "",
            playing_style=profile.playing_style or "",
            budget_tier=profile.budget_tier or "between_30_50",
            preferred_tension=profile.preferred_tension or 0,
            game_type=profile.game_type or "",
            frequency_per_week=profile.frequency_per_week or 0,
            pref_attack=profile.pref_attack or 0,
            pref_comfort=profile.pref_comfort or 0,
            pref_control=profile.pref_control or 0,
            pref_durability=profile.pref_durability or 0,
            pref_elasticity=profile.pref_elasticity or 0,
            pref_sound=profile.pref_sound or 0,
            pref_string_movement=profile.pref_string_movement or 0,
            pref_tension_retention=profile.pref_tension_retention or 0,
            pref_value_for_money=profile.pref_value_for_money or 0,
            top_n=top_n,
            budget_min=profile.budget_min,
            budget_max=profile.budget_max,
        )
        return self._execute(user_id=user_id, request=request, persist=True)

    def execute_cached(self, *, user_id: str) -> RecommendationResponseModel:
        cached = self.recommendation_repository.get_cached_results(user_id=user_id)
        if not cached:
            raise NotFoundError("No cached recommendations found")
        return RecommendationResponseModel(
            algorithm_version=cached[0].algorithm_version,
            results=[self._record_to_result(item) for item in cached],
            generated_at=cached[0].generated_at,
        )

    def execute_detail(
        self,
        *,
        user_id: str,
        catalog_id: str,
    ) -> RecommendationDetailModel:
        cached = self.recommendation_repository.get_cached_result_detail(
            user_id=user_id,
            catalog_id=catalog_id,
        )
        if cached is None:
            raise NotFoundError("No cached recommendation detail found")
        return RecommendationDetailModel(
            algorithm_version=cached.algorithm_version,
            result=self._record_to_result(cached),
            generated_at=cached.generated_at,
        )

    def _execute(
        self,
        *,
        user_id: str | None,
        request: RecommendationRequestModel,
        persist: bool,
    ) -> RecommendationResponseModel:
        scored_results = self.scorer.score_candidates(
            candidates=self.recommendation_repository.list_active_candidates(),
            request=request,
            top_n=request.top_n,
        )
        result_models = [item.result for item in scored_results]
        generated_at = None

        if persist and user_id:
            self.recommendation_repository.replace_user_preference_vector(
                user_id=user_id,
                source_layer=PREFERENCE_SOURCE_LAYER,
                entries=scored_results[0].preference_vector_rows
                if scored_results
                else [],
            )
            cached = self.recommendation_repository.replace_score_cache(
                user_id=user_id,
                algorithm_version=ALGORITHM_VERSION,
                results=[item.cache_payload for item in scored_results],
            )
            generated_at = cached[0].generated_at if cached else None
            cached_by_catalog = {item.catalog_id: item for item in cached}
            result_models = [
                self._merge_cached_result(
                    result=result,
                    cached=cached_by_catalog.get(result.catalog_id or ""),
                )
                for result in result_models
            ]

        response = RecommendationResponseModel(
            algorithm_version=ALGORITHM_VERSION,
            results=result_models,
            generated_at=generated_at,
        )
        result_payloads = [_result_payload(item) for item in response.results]
        response_payload = {
            "algorithm_version": response.algorithm_version,
            "generated_at": response.generated_at.isoformat()
            if response.generated_at
            else None,
            "results": result_payloads,
        }
        self.recommendation_log_repository.create_run(
            user_id=user_id,
            request_payload=request.__dict__,
            profile_payload=request.__dict__,
            result_payloads=result_payloads,
            algorithm_version=response.algorithm_version,
            matrix_version=_matrix_version_from_results(result_payloads),
            feature_source_version=_feature_source_version_from_results(
                result_payloads
            ),
        )
        self.recommendation_log_repository.create_log(
            user_id=user_id,
            request_payload=request.__dict__,
            response_payload=response_payload,
            algorithm_version=response.algorithm_version,
        )
        return response

    def _merge_cached_result(
        self,
        *,
        result: RecommendationResultModel,
        cached: CachedRecommendationRecord | None,
    ) -> RecommendationResultModel:
        if cached is None:
            return result
        breakdown = dict(result.score_breakdown or {})
        if cached.preference_match_score is not None:
            breakdown.setdefault("preference_match", cached.preference_match_score)
        if cached.rule_fit_score is not None:
            breakdown.setdefault("rule_fit", cached.rule_fit_score)
        if cached.budget_fit_score is not None:
            breakdown.setdefault("budget_fit", cached.budget_fit_score)
        if cached.confidence_score is not None:
            breakdown.setdefault("confidence_score", cached.confidence_score)
        if cached.nlp_review_score is not None:
            breakdown.setdefault("nlp_review_score", cached.nlp_review_score)
        breakdown.setdefault("final_score", cached.final_score)
        rationale = dict(result.rationale_payload or {})
        rationale.setdefault("score_breakdown", breakdown)
        return RecommendationResultModel(
            rank=result.rank,
            string_name=result.string_name,
            brand=result.brand,
            score=result.score,
            price_rm=result.price_rm,
            aspect_scores=result.aspect_scores,
            reasons=result.reasons,
            catalog_id=result.catalog_id,
            model_name=result.model_name,
            score_breakdown=breakdown,
            rationale_payload=rationale,
            generated_at=cached.generated_at,
        )

    def _record_to_result(
        self,
        item: CachedRecommendationRecord,
    ) -> RecommendationResultModel:
        rationale = dict(item.rationale or {})
        breakdown = dict(rationale.get("score_breakdown") or {})
        if not breakdown:
            breakdown = {
                "preference_match": item.preference_match_score,
                "rule_fit": item.rule_fit_score,
                "budget_fit": item.budget_fit_score,
                "confidence_score": item.confidence_score,
                "nlp_review_score": item.nlp_review_score,
                "final_score": item.final_score,
            }
        aspect_scores = dict(rationale.get("fused_feature_scores") or {})
        return RecommendationResultModel(
            rank=item.rank_position,
            string_name=str(rationale.get("display_name") or item.catalog_id),
            brand=str(rationale.get("brand") or ""),
            model_name=rationale.get("model_name")
            if isinstance(rationale.get("model_name"), str)
            else None,
            catalog_id=item.catalog_id,
            score=item.final_score,
            price_rm=_float_or_none(rationale.get("budget", {}).get("price_rm"))
            if isinstance(rationale.get("budget"), dict)
            else None,
            aspect_scores={
                key: float(value)
                for key, value in aspect_scores.items()
                if key
                in {
                    "repulsion",
                    "comfort",
                    "control",
                    "durability",
                    "elasticity",
                    "sound",
                    "string_movement",
                    "tension_retention",
                }
            },
            reasons=list(
                rationale.get("top_reasons") or rationale.get("reasons") or []
            ),
            score_breakdown={
                key: float(value)
                for key, value in breakdown.items()
                if value is not None
            },
            rationale_payload=rationale,
            generated_at=item.generated_at,
        )


def _float_or_none(value: object) -> float | None:
    if value is None:
        return None
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value, got {type(value).__name__}")


def _result_payload(item: RecommendationResultModel) -> dict[str, object]:
    return {
        "rank": item.rank,
        "catalog_id": item.catalog_id,
        "string_name": item.string_name,
        "brand": item.brand,
        "model_name": item.model_name,
        "score": item.score,
        "price_rm": item.price_rm,
        "aspect_scores": item.aspect_scores,
        "reasons": item.reasons,
        "score_breakdown": item.score_breakdown or {},
        "rationale_payload": item.rationale_payload or {},
        "generated_at": item.generated_at.isoformat() if item.generated_at else None,
    }


def _matrix_version_from_results(
    result_payloads: list[dict[str, object]],
) -> str | None:
    for item in result_payloads:
        rationale = item.get("rationale_payload")
        if isinstance(rationale, dict):
            value = rationale.get("matrix_version")
            if isinstance(value, str):
                return value
    return None


def _feature_source_version_from_results(
    result_payloads: list[dict[str, object]],
) -> str | None:
    for item in result_payloads:
        rationale = item.get("rationale_payload")
        if isinstance(rationale, dict):
            value = rationale.get("feature_source_version")
            if isinstance(value, str):
                return value
    return None
