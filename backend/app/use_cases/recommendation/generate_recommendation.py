from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from uuid import uuid4

from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationDetailModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResponseModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.entities import RacketRecommendationContext
from app.domain.recommendation.learning_signals import build_cf_evidence
from app.domain.recommendation.learning_signals import build_feedback_snapshot
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.domain.recommendation.scoring import ContentRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.ports.repositories.profile_repository import ProfileRepository
from app.ports.repositories.recommendation_log_repository import (
    RecommendationLogRepository,
)
from app.ports.repositories.recommendation_repository import RecommendationRepository
from app.shared.errors import BadRequestError
from app.shared.errors import ConflictError
from app.shared.errors import NotFoundError


REQUIRED_PROFILE_FIELDS = {
    "skill_level",
    "playing_style",
    "preferred_tension",
    "frequency_per_week",
    "preferred_feel",
    "preferred_gauge",
    "recent_goal",
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
    scorer: ContentRecommendationScorer = field(
        default_factory=ContentRecommendationScorer
    )

    def execute_preview(
        self,
        *,
        user_id: str | None,
        request: RecommendationRequestModel,
        racket_id: str | None = None,
    ) -> RecommendationResponseModel:
        racket_context = None
        if racket_id is not None:
            if user_id is None:
                raise BadRequestError("A player is required for racket context")
            racket_context = self.recommendation_repository.get_owned_racket_context(
                user_id=user_id,
                racket_id=racket_id,
                target_tension=request.preferred_tension,
            )
            if racket_context is None:
                raise NotFoundError("Racket not found")
        return self._execute(
            user_id=user_id,
            request=request,
            persist=False,
            profile_snapshot=None,
            racket_context=racket_context,
        )

    def execute_profile(
        self,
        *,
        user_id: str,
        top_n: int,
        racket_id: str | None = None,
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
            preferred_tension=profile.preferred_tension or 0,
            frequency_per_week=profile.frequency_per_week or 0,
            preferred_feel=profile.preferred_feel or "medium",
            preferred_gauge=profile.preferred_gauge or "no_preference",
            recent_goal=profile.recent_goal or "balanced",
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
        )
        racket_context = None
        if racket_id is not None:
            racket_context = self.recommendation_repository.get_owned_racket_context(
                user_id=user_id,
                racket_id=racket_id,
                target_tension=request.preferred_tension,
            )
            if racket_context is None:
                raise NotFoundError("Racket not found")
        return self._execute(
            user_id=user_id,
            request=request,
            persist=True,
            profile_snapshot={
                **_profile_snapshot(profile),
                "racket_context": _racket_context_payload(racket_context),
            },
            racket_context=racket_context,
        )

    def execute_cached(self, *, user_id: str) -> RecommendationResponseModel:
        cached = self.recommendation_repository.get_cached_results(
            user_id=user_id,
            algorithm_version=ALGORITHM_VERSION,
        )
        if not cached:
            raise NotFoundError("No cached recommendations found")
        if not self._cache_is_current(cached):
            raise NotFoundError("No current cached recommendations found")
        return RecommendationResponseModel(
            algorithm_version=cached[0].algorithm_version,
            results=[self._record_to_result(item) for item in cached],
            run_id=_cached_run_id(cached[0]),
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
            algorithm_version=ALGORITHM_VERSION,
        )
        if cached is None:
            raise NotFoundError("No cached recommendation detail found")
        if not self._cache_is_current([cached]):
            raise NotFoundError("No current cached recommendation detail found")
        return RecommendationDetailModel(
            algorithm_version=cached.algorithm_version,
            result=self._record_to_result(cached),
            run_id=_cached_run_id(cached),
            generated_at=cached.generated_at,
        )

    def _execute(
        self,
        *,
        user_id: str | None,
        request: RecommendationRequestModel,
        persist: bool,
        profile_snapshot: dict[str, object] | None = None,
        racket_context: RacketRecommendationContext | None = None,
    ) -> RecommendationResponseModel:
        feedback_snapshot = build_feedback_snapshot(
            self.recommendation_repository.list_feedback_rows(),
            target_racket_model_key=(
                racket_context.model_key if racket_context is not None else None
            ),
        )
        cf_evidence = build_cf_evidence(
            self.recommendation_repository.list_recommendation_interactions(),
            current_user_id=user_id or "",
            current_preference_vector=_request_preference_vector(request),
            target_racket_model_key=(
                racket_context.model_key if racket_context is not None else None
            ),
            target_tension=request.preferred_tension,
        )
        scored_results = self.scorer.score_candidates(
            candidates=self.recommendation_repository.list_active_candidates(),
            request=request,
            top_n=request.top_n,
            feedback_snapshot=feedback_snapshot,
            cf_evidence=cf_evidence,
            racket_context=racket_context,
        )
        run_id = str(uuid4())
        result_models = [item.result for item in scored_results]
        generated_at = None

        if persist and user_id:
            latest_feedback = build_feedback_snapshot(
                self.recommendation_repository.list_feedback_rows(),
                target_racket_model_key=(
                    racket_context.model_key if racket_context is not None else None
                ),
            )
            latest_cf = build_cf_evidence(
                self.recommendation_repository.list_recommendation_interactions(),
                current_user_id=user_id,
                current_preference_vector=_request_preference_vector(request),
                target_racket_model_key=(
                    racket_context.model_key if racket_context is not None else None
                ),
                target_tension=request.preferred_tension,
            )
            if (
                latest_feedback.snapshot_version != feedback_snapshot.snapshot_version
                or latest_cf.source_version != cf_evidence.source_version
            ):
                raise ConflictError("Recommendation evidence changed; retry generation")
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
                results=[
                    _cache_payload_with_run_id(item.cache_payload, run_id)
                    for item in scored_results
                ],
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
            run_id=run_id,
            generated_at=generated_at,
        )
        result_payloads = [_result_payload(item) for item in response.results]
        response_payload = {
            "algorithm_version": response.algorithm_version,
            "run_id": response.run_id,
            "generated_at": response.generated_at.isoformat()
            if response.generated_at
            else None,
            "results": result_payloads,
        }
        request_snapshot = {
            **request.__dict__,
            "racket_context": _racket_context_payload(racket_context),
        }
        self.recommendation_log_repository.create_run(
            run_id=run_id,
            user_id=user_id,
            request_payload=request_snapshot,
            profile_payload=profile_snapshot or request.__dict__,
            result_payloads=result_payloads,
            algorithm_version=response.algorithm_version,
        )
        self.recommendation_log_repository.create_log(
            user_id=user_id,
            request_payload=request_snapshot,
            response_payload=response_payload,
            algorithm_version=response.algorithm_version,
        )
        return response

    def _cache_is_current(self, cached: list[CachedRecommendationRecord]) -> bool:
        if not cached:
            return False
        rationale = cached[0].rationale
        racket_payload = rationale.get("racket_context")
        model_key = (
            str(racket_payload.get("normalized_model_key"))
            if isinstance(racket_payload, dict)
            and racket_payload.get("normalized_model_key")
            else None
        )
        feedback_snapshot = build_feedback_snapshot(
            self.recommendation_repository.list_feedback_rows(),
            target_racket_model_key=model_key,
        )
        if (
            rationale.get("feedback_snapshot_version")
            != feedback_snapshot.snapshot_version
        ):
            return False

        cf_payload = rationale.get("cf_shadow")
        expected_cf_version = (
            cf_payload.get("source_version") if isinstance(cf_payload, dict) else None
        )
        current_cf = build_cf_evidence(
            self.recommendation_repository.list_recommendation_interactions(),
            current_user_id=cached[0].user_id,
            current_preference_vector=(1,) * 9,
            target_racket_model_key=model_key,
            target_tension=0,
        )
        return expected_cf_version == current_cf.source_version

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
        if cached.value_for_money_score is not None:
            breakdown.setdefault("value_for_money", cached.value_for_money_score)
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
                "value_for_money": item.value_for_money_score,
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
            price_rm=_cached_price(rationale),
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
                    "value_for_money",
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


def _cached_run_id(item: CachedRecommendationRecord) -> str | None:
    value = item.rationale.get("run_id")
    return value if isinstance(value, str) and value else None


def _cache_payload_with_run_id(
    payload: dict[str, object],
    run_id: str,
) -> dict[str, object]:
    raw_rationale = payload.get("rationale")
    rationale = dict(raw_rationale) if isinstance(raw_rationale, dict) else {}
    rationale["run_id"] = run_id
    return {**payload, "rationale": rationale}


def _cached_price(rationale: dict[str, object]) -> float | None:
    if "price_rm" in rationale:
        return _float_or_none(rationale.get("price_rm"))
    legacy_budget = rationale.get("budget")
    if isinstance(legacy_budget, dict):
        return _float_or_none(legacy_budget.get("price_rm"))
    return None


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


def _profile_snapshot(profile) -> dict[str, object]:
    return {
        "user_id": profile.user_id,
        "skill_level": profile.skill_level,
        "playing_style": profile.playing_style,
        "preferred_tension": profile.preferred_tension,
        "frequency_per_week": profile.frequency_per_week,
        "preferred_feel": profile.preferred_feel,
        "preferred_gauge": profile.preferred_gauge,
        "recent_goal": profile.recent_goal,
        "pref_attack": profile.pref_attack,
        "pref_comfort": profile.pref_comfort,
        "pref_control": profile.pref_control,
        "pref_durability": profile.pref_durability,
        "pref_elasticity": profile.pref_elasticity,
        "pref_sound": profile.pref_sound,
        "pref_string_movement": profile.pref_string_movement,
        "pref_tension_retention": profile.pref_tension_retention,
        "pref_value_for_money": profile.pref_value_for_money,
        "created_at": _isoformat_or_none(profile.created_at),
        "updated_at": _isoformat_or_none(profile.updated_at),
    }


def _request_preference_vector(request: RecommendationRequestModel) -> tuple[int, ...]:
    return (
        request.pref_attack,
        request.pref_comfort,
        request.pref_control,
        request.pref_durability,
        request.pref_elasticity,
        request.pref_sound,
        request.pref_string_movement,
        request.pref_tension_retention,
        request.pref_value_for_money,
    )


def _racket_context_payload(
    context: RacketRecommendationContext | None,
) -> dict[str, object] | None:
    if context is None:
        return None
    return {
        "racket_id": context.racket_id,
        "brand": context.brand,
        "model": context.model,
        "normalized_model_key": context.model_key,
        "target_tension": context.target_tension,
    }


def _isoformat_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None
