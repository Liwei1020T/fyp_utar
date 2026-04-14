from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationFeatureSignalModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResultModel


ALGORITHM_VERSION = "fyp1_similarity_confidence_rule_budget_tier_v5"
MATRIX_VERSION = "latest_practical_string_feature_matrix_v9_v8dict"
FEATURE_SOURCE_VERSION = "absa_v8_practical_matrix_v9"
PREFERENCE_SOURCE_LAYER = "profile"

CORE_RECOMMENDATION_FEATURES = (
    "repulsion",
    "control",
    "durability",
    "comfort",
    "sound",
    "elasticity",
    "tension_retention",
    "string_movement",
)
SUPPORT_FEATURES = (
    "value_for_money",
    "stability_score",
    "beginner_fit_score",
    "attacking_fit_score",
    "control_fit_score",
    "all_round_score",
)
ALL_FEATURES = CORE_RECOMMENDATION_FEATURES + SUPPORT_FEATURES

FEATURE_LABELS = {
    "repulsion": "power and rebound",
    "comfort": "comfort",
    "control": "control",
    "durability": "durability",
    "sound": "hitting sound",
    "elasticity": "elastic rebound",
    "tension_retention": "tension retention",
    "string_movement": "string movement control",
}

FEATURE_PRIORS = {
    "repulsion": 0.58,
    "control": 0.55,
    "durability": 0.57,
    "comfort": 0.56,
    "sound": 0.54,
    "elasticity": 0.55,
    "tension_retention": 0.54,
    "string_movement": 0.53,
}

FINAL_SCORE_WEIGHTS = {
    "preference_match": 0.60,
    "rule_fit": 0.15,
    "budget_fit": 0.15,
    "confidence_score": 0.10,
}

BUDGET_TIER_TO_BOUNDS = {
    "below_30": {"min_rm": 0.0, "max_rm": 30.0},
    "between_30_50": {"min_rm": 30.0, "max_rm": 50.0},
    "above_50": {"min_rm": 50.0, "max_rm": 999.0},
}

BUDGET_TIER_FIT_SCORES = {
    "below_30": {"low": 1.00, "mid": 0.58, "high": 0.25, "unknown": 0.45},
    "between_30_50": {"low": 0.78, "mid": 1.00, "high": 0.56, "unknown": 0.45},
    "above_50": {"low": 0.60, "mid": 0.80, "high": 1.00, "unknown": 0.45},
}

PRICE_TIER_LABELS = {
    "low": "low-price tier",
    "mid": "mid-price tier",
    "high": "high-price tier",
    "unknown": "unknown-price tier",
}


@dataclass(frozen=True)
class ScoredRecommendation:
    result: RecommendationResultModel
    cache_payload: dict[str, object]
    preference_vector_rows: list[dict[str, float | str | None]]


class Fyp1ContentRecommendationScorer:
    """FYP1 scorer: rule-enhanced, confidence-aware, content-based, explainable."""

    def build_preference_vector(
        self,
        *,
        user_id: str,
        request: RecommendationRequestModel,
    ) -> list[dict[str, float | str | None]]:
        raw_scores = {
            "repulsion": float(request.pref_attack),
            "control": float(request.pref_control),
            "durability": float(request.pref_durability),
            "comfort": float(request.pref_comfort),
            "sound": float(request.pref_sound),
            "elasticity": float(request.pref_elasticity),
            "tension_retention": float(request.pref_tension_retention),
            "string_movement": float(request.pref_string_movement),
        }
        total_weight = sum(raw_scores.values()) or 1.0
        return [
            {
                "feature_key": feature_key,
                "raw_score": raw_score,
                "preference_weight": round(raw_score / total_weight, 4),
                "preferred_min": None,
                "preferred_max": None,
            }
            for feature_key, raw_score in raw_scores.items()
        ]

    def score_candidates(
        self,
        *,
        candidates: list[RecommendationCandidateModel],
        request: RecommendationRequestModel,
        top_n: int,
    ) -> list[ScoredRecommendation]:
        preference_vector_rows = self.build_preference_vector(
            user_id=request.user_id or "",
            request=request,
        )

        scored: list[ScoredRecommendation] = []
        for candidate in candidates:
            effective_scores, feature_sources, feature_meta = _effective_item_features(
                candidate
            )
            feature_evidence = _build_feature_evidence(
                effective_scores=effective_scores,
                feature_sources=feature_sources,
                feature_meta=feature_meta,
                preference_rows=preference_vector_rows,
            )
            auxiliary_scores = _auxiliary_scores(candidate)
            preference_match = _preference_match_score(
                effective_scores=effective_scores,
                preference_rows=preference_vector_rows,
            )
            nlp_review_score = _nlp_review_alignment_score(
                feature_evidence=feature_evidence,
                preference_rows=preference_vector_rows,
            )
            item_price_tier = _item_price_tier(candidate.item.price_rm)
            budget_fit = _budget_fit_score(candidate.item.price_rm, request.budget_tier)
            rule_fit, rule_reasons, rule_events = _rule_fit_score(
                item=candidate.item,
                effective_scores=effective_scores,
                auxiliary_scores=auxiliary_scores,
                request=request,
            )
            confidence_score = _confidence_score(
                feature_evidence=feature_evidence,
                feature_sources=feature_sources,
            )
            final_score = round(
                clamp01(
                    (preference_match * FINAL_SCORE_WEIGHTS["preference_match"])
                    + (rule_fit * FINAL_SCORE_WEIGHTS["rule_fit"])
                    + (budget_fit * FINAL_SCORE_WEIGHTS["budget_fit"])
                    + (confidence_score * FINAL_SCORE_WEIGHTS["confidence_score"])
                ),
                4,
            )

            reasons = _build_reasons(
                item=candidate.item,
                request=request,
                effective_scores=effective_scores,
                preference_rows=preference_vector_rows,
                budget_fit=budget_fit,
                item_price_tier=item_price_tier,
                confidence_score=confidence_score,
                rule_reasons=rule_reasons,
            )
            breakdown = {
                "preference_match": round(preference_match, 4),
                "rule_fit": round(rule_fit, 4),
                "budget_fit": round(budget_fit, 4),
                "confidence_score": round(confidence_score, 4),
                "final_score": final_score,
            }
            if nlp_review_score is not None:
                breakdown["nlp_review_score"] = round(nlp_review_score, 4)

            fit_angle = _primary_fit_angle(
                effective_scores,
                auxiliary_scores,
                request,
                budget_fit=budget_fit,
                confidence_score=confidence_score,
            )
            rationale_payload = {
                "catalog_id": candidate.item.id,
                "display_name": candidate.item.display_name,
                "brand": candidate.item.brand,
                "model_name": candidate.item.model_name,
                "matrix_version": MATRIX_VERSION,
                "feature_source_version": FEATURE_SOURCE_VERSION,
                "review_count_snapshot": candidate.item.review_count,
                "algorithm_family": (
                    "rule_enhanced_confidence_aware_content_based_official_nlp_budget_tier"
                ),
                "collaborative_filtering_used": False,
                "primary_fit_angle": fit_angle,
                "trade_off_summary": _trade_off_summary(
                    effective_scores,
                    breakdown,
                    request,
                ),
                "top_reasons": reasons,
                "score_breakdown": breakdown,
                "feature_sources": feature_sources,
                "feature_evidence": feature_evidence,
                "effective_feature_scores": {
                    key: round(value, 4) for key, value in effective_scores.items()
                },
                "fused_feature_scores": {
                    key: round(value, 4) for key, value in effective_scores.items()
                },
                "auxiliary_scores": {
                    key: round(value, 4) for key, value in auxiliary_scores.items()
                },
                "user_preference_vector": [
                    {
                        "feature_key": str(row["feature_key"]),
                        "raw_score": row.get("raw_score"),
                        "preference_weight": row.get("preference_weight"),
                    }
                    for row in preference_vector_rows
                ],
                "nlp_review_scores": {
                    key: round(score, 4)
                    for key, value in candidate.matrix_by_source.get(
                        "nlp_review", {}
                    ).items()
                    if (score := _signal_score(value)) is not None
                },
                "nlp_review_signal_count": sum(
                    [
                        1
                        for row in feature_evidence
                        if (_to_float(row.get("nlp_influence")) or 0) > 0
                    ]
                ),
                "nlp_review_summary": _nlp_review_summary(feature_evidence),
                "budget": {
                    "price_rm": candidate.item.price_rm,
                    "budget_tier": request.budget_tier,
                    "item_price_tier": item_price_tier,
                    "budget_tier_bounds_rm": BUDGET_TIER_TO_BOUNDS.get(
                        request.budget_tier,
                        BUDGET_TIER_TO_BOUNDS["between_30_50"],
                    ),
                },
                "rule_events": rule_events,
                "profile_context": {
                    "skill_level": request.skill_level,
                    "playing_style": request.playing_style,
                    "budget_tier": request.budget_tier,
                    "preferred_tension": request.preferred_tension,
                    "game_type": request.game_type,
                    "frequency_per_week": request.frequency_per_week,
                },
            }
            result = RecommendationResultModel(
                rank=0,
                string_name=candidate.item.display_name,
                brand=candidate.item.brand,
                model_name=candidate.item.model_name,
                catalog_id=candidate.item.id,
                score=final_score,
                price_rm=candidate.item.price_rm,
                aspect_scores={
                    feature_key: round(
                        effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]),
                        4,
                    )
                    for feature_key in CORE_RECOMMENDATION_FEATURES
                },
                reasons=reasons,
                score_breakdown=breakdown,
                rationale_payload=rationale_payload,
            )
            scored.append(
                ScoredRecommendation(
                    result=result,
                    cache_payload={
                        "catalog_id": candidate.item.id,
                        "preference_match_score": breakdown["preference_match"],
                        "rule_fit_score": breakdown["rule_fit"],
                        "budget_fit_score": breakdown["budget_fit"],
                        "confidence_score": breakdown["confidence_score"],
                        "nlp_review_score": breakdown.get("nlp_review_score"),
                        "final_score": final_score,
                        "rank_position": 0,
                        "rationale": rationale_payload,
                        "matrix_version": MATRIX_VERSION,
                        "feature_source_version": FEATURE_SOURCE_VERSION,
                    },
                    preference_vector_rows=preference_vector_rows,
                )
            )

        ranked = sorted(
            scored,
            key=lambda item: (
                -item.result.score,
                item.result.price_rm
                if item.result.price_rm is not None
                else float("inf"),
                item.result.brand,
                item.result.model_name or item.result.string_name,
            ),
        )
        final_ranked: list[ScoredRecommendation] = []
        for index, entry in enumerate(ranked[:top_n], start=1):
            final_ranked.append(
                ScoredRecommendation(
                    result=RecommendationResultModel(
                        rank=index,
                        string_name=entry.result.string_name,
                        brand=entry.result.brand,
                        score=entry.result.score,
                        price_rm=entry.result.price_rm,
                        aspect_scores=entry.result.aspect_scores,
                        reasons=entry.result.reasons,
                        catalog_id=entry.result.catalog_id,
                        model_name=entry.result.model_name,
                        score_breakdown=entry.result.score_breakdown,
                        rationale_payload=entry.result.rationale_payload,
                        generated_at=entry.result.generated_at,
                    ),
                    cache_payload={
                        **entry.cache_payload,
                        "rank_position": index,
                    },
                    preference_vector_rows=entry.preference_vector_rows,
                )
            )
        return final_ranked


def _effective_item_features(
    candidate: RecommendationCandidateModel,
) -> tuple[dict[str, float], dict[str, str], dict[str, dict[str, object]]]:
    official_scores = _official_feature_scores(candidate.item)
    nlp_scores = candidate.matrix_by_source.get("nlp_review", {})
    nlp_feature_signals = {
        feature_key: _nlp_feature_signal(nlp_scores, feature_key)
        for feature_key in CORE_RECOMMENDATION_FEATURES
    }

    official_coverage = len(official_scores) / len(CORE_RECOMMENDATION_FEATURES)
    nlp_coverage = sum(
        1 for value in nlp_feature_signals.values() if value is not None
    ) / len(CORE_RECOMMENDATION_FEATURES)
    nlp_support_count = sum(
        1
        for feature_key in SUPPORT_FEATURES
        if (signal := nlp_scores.get(feature_key)) is not None
        and _signal_score(signal) is not None
    )

    official_confidence_global = clamp01(0.62 + (official_coverage * 0.28))
    review_count_confidence = _review_count_confidence(candidate.item.review_count)
    nlp_confidence_global = clamp01(
        0.18
        + (nlp_coverage * 0.35)
        + (min(nlp_support_count, 3) / 3 * 0.12)
        + (review_count_confidence * 0.20)
    )

    effective: dict[str, float] = {}
    sources: dict[str, str] = {}
    feature_meta: dict[str, dict[str, object]] = {}

    for feature_key in CORE_RECOMMENDATION_FEATURES:
        prior_score = FEATURE_PRIORS[feature_key]
        official_value = official_scores.get(feature_key)
        nlp_signal = nlp_feature_signals.get(feature_key)
        nlp_value = _signal_score(nlp_signal) if nlp_signal is not None else None
        nlp_feature_confidence = (
            _signal_confidence(nlp_signal) if nlp_signal is not None else None
        )

        nlp_influence = 0.0
        source_confidence = 0.16
        fused_base = prior_score

        if official_value is not None and nlp_value is not None:
            source = "official_performance+nlp_review"
            official_confidence = official_confidence_global
            nlp_confidence = clamp01(
                0.18
                + ((nlp_feature_confidence or nlp_confidence_global) * 0.62)
                + (review_count_confidence * 0.10)
            )
            weight_total = max(official_confidence + nlp_confidence, 1e-6)
            fused_base = (
                (official_value * official_confidence) + (nlp_value * nlp_confidence)
            ) / weight_total
            source_confidence = clamp01(min(0.95, 0.45 + (weight_total / 2)))
            nlp_influence = clamp01(nlp_confidence / weight_total)
        elif official_value is not None:
            source = "official_performance"
            fused_base = official_value
            source_confidence = clamp01(official_confidence_global * 0.95)
        elif nlp_value is not None:
            source = "nlp_review"
            fused_base = nlp_value
            nlp_confidence = clamp01(
                0.14
                + ((nlp_feature_confidence or nlp_confidence_global) * 0.58)
                + (review_count_confidence * 0.12)
            )
            source_confidence = clamp01(nlp_confidence * 0.78)
            nlp_influence = 1.0
        else:
            source = "prior_fallback"

        effective_score = clamp01(
            (fused_base * source_confidence) + (prior_score * (1 - source_confidence))
        )
        missing_data_penalty = round((1 - source_confidence) * 0.12, 4)

        effective[feature_key] = effective_score
        sources[feature_key] = source
        feature_meta[feature_key] = {
            "official_score": official_value,
            "nlp_review_score": nlp_value,
            "nlp_confidence": nlp_feature_confidence,
            "nlp_influence": nlp_influence,
            "fusion_confidence": source_confidence,
            "prior_score": prior_score,
            "missing_data_penalty": missing_data_penalty,
            "source_version": _signal_source_version(nlp_signal),
            "source_ref": _signal_source_ref(nlp_signal),
            "review_count_snapshot": _signal_review_count_snapshot(nlp_signal)
            or candidate.item.review_count,
        }

    return effective, sources, feature_meta


def _official_feature_scores(item: StringItem) -> dict[str, float]:
    official = item.official_performance
    if official is None:
        return {}

    scores: dict[str, float] = {}
    if official.repulsion_power is not None:
        scores["repulsion"] = official.repulsion_power / 10
    if official.shock_absorption is not None:
        scores["comfort"] = official.shock_absorption / 10
    if official.control is not None:
        scores["control"] = official.control / 10
    if official.durability is not None:
        scores["durability"] = official.durability / 10
    if official.hitting_sound is not None:
        scores["sound"] = official.hitting_sound / 10

    return {key: clamp01(value) for key, value in scores.items()}


def _nlp_feature_signal(
    nlp_scores: Mapping[str, float | RecommendationFeatureSignalModel],
    feature_key: str,
) -> float | RecommendationFeatureSignalModel | None:
    aliases = {
        "repulsion": ("repulsion", "attack"),
        "sound": ("sound", "hitting_sound"),
    }.get(feature_key, (feature_key,))

    for alias in aliases:
        value = nlp_scores.get(alias)
        if value is not None:
            return value
    return None


def _auxiliary_scores(candidate: RecommendationCandidateModel) -> dict[str, float]:
    scores: dict[str, float] = {}
    for source_layer in ("nlp_review", "hybrid_derived", "community_signal"):
        for feature_key, value in candidate.matrix_by_source.get(
            source_layer, {}
        ).items():
            if feature_key in SUPPORT_FEATURES and feature_key not in scores:
                score = _signal_score(value)
                if score is not None:
                    scores[feature_key] = score
    return scores


def _build_feature_evidence(
    *,
    effective_scores: dict[str, float],
    feature_sources: dict[str, str],
    feature_meta: dict[str, dict[str, object]],
    preference_rows: list[dict[str, float | str | None]],
) -> list[dict[str, object]]:
    preference_weights = {
        str(row["feature_key"]): round(float(row.get("preference_weight") or 0), 4)
        for row in preference_rows
    }
    rows: list[dict[str, object]] = []

    for feature_key in CORE_RECOMMENDATION_FEATURES:
        meta = feature_meta.get(feature_key, {})
        row = {
            "feature_key": feature_key,
            "display_label": FEATURE_LABELS[feature_key].title(),
            "effective_score": round(
                effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]),
                4,
            ),
            "preference_weight": preference_weights.get(feature_key, 0.0),
            "source": feature_sources.get(feature_key, "prior_fallback"),
            "official_score": round(_to_float(meta.get("official_score")) or 0.0, 4)
            if _to_float(meta.get("official_score")) is not None
            else None,
            "nlp_review_score": round(
                _to_float(meta.get("nlp_review_score")) or 0.0,
                4,
            )
            if _to_float(meta.get("nlp_review_score")) is not None
            else None,
            "nlp_confidence": round(
                _to_float(meta.get("nlp_confidence")) or 0.0,
                4,
            )
            if _to_float(meta.get("nlp_confidence")) is not None
            else None,
            "nlp_influence": round(_to_float(meta.get("nlp_influence")) or 0.0, 4),
            "fusion_confidence": round(
                _to_float(meta.get("fusion_confidence")) or 0.0,
                4,
            ),
            "prior_score": round(_to_float(meta.get("prior_score")) or 0.0, 4),
            "missing_data_penalty": round(
                _to_float(meta.get("missing_data_penalty")) or 0.0,
                4,
            ),
            "source_version": meta.get("source_version"),
            "source_ref": meta.get("source_ref"),
            "review_count_snapshot": meta.get("review_count_snapshot"),
        }
        rows.append(row)

    rows.sort(
        key=lambda row: (
            -(
                (_to_float(row.get("preference_weight")) or 0)
                * (_to_float(row.get("effective_score")) or 0)
                * max(_to_float(row.get("fusion_confidence")) or 0, 0.3)
            ),
            -(_to_float(row.get("effective_score")) or 0),
        )
    )
    return rows


def _confidence_score(
    *,
    feature_evidence: list[dict[str, object]],
    feature_sources: dict[str, str],
) -> float:
    if not feature_evidence:
        return 0.3

    coverage_ratio = _feature_coverage(feature_sources)
    average_fusion_confidence = sum(
        (_to_float(row.get("fusion_confidence")) or 0) for row in feature_evidence
    ) / len(feature_evidence)
    strong_support_ratio = sum(
        1
        for row in feature_evidence
        if (_to_float(row.get("fusion_confidence")) or 0) >= 0.7
    ) / len(feature_evidence)
    nlp_signal_ratio = sum(
        1 for row in feature_evidence if (_to_float(row.get("nlp_influence")) or 0) > 0
    ) / len(feature_evidence)
    fallback_ratio = sum(
        1 for source in feature_sources.values() if source == "prior_fallback"
    ) / len(feature_sources)

    has_official = any(
        source in {"official_performance", "official_performance+nlp_review"}
        for source in feature_sources.values()
    )
    has_nlp = any(
        source in {"nlp_review", "official_performance+nlp_review"}
        for source in feature_sources.values()
    )
    source_blend_bonus = 0.05 if has_official and has_nlp else 0.0

    score = (
        (coverage_ratio * 0.38)
        + (average_fusion_confidence * 0.28)
        + (strong_support_ratio * 0.18)
        + (nlp_signal_ratio * 0.16)
        + source_blend_bonus
        - (fallback_ratio * 0.22)
    )
    return clamp01(score)


def _feature_coverage(feature_sources: dict[str, str]) -> float:
    if not feature_sources:
        return 0.0
    covered = sum(
        1 for source in feature_sources.values() if source != "prior_fallback"
    )
    return covered / len(feature_sources)


def _nlp_review_alignment_score(
    *,
    feature_evidence: list[dict[str, object]],
    preference_rows: list[dict[str, float | str | None]],
) -> float | None:
    total_weight = sum(
        float(row.get("preference_weight") or 0)
        for row in preference_rows
        if str(row["feature_key"]) in CORE_RECOMMENDATION_FEATURES
    )
    if total_weight <= 0:
        return None

    weighted_signal = 0.0
    influence_weight = 0.0
    for row in feature_evidence:
        nlp_score = _to_float(row.get("nlp_review_score"))
        nlp_influence = _to_float(row.get("nlp_influence")) or 0
        preference_weight = _to_float(row.get("preference_weight")) or 0
        if nlp_score is None or nlp_influence <= 0:
            continue
        weighted_signal += nlp_score * preference_weight * nlp_influence
        influence_weight += preference_weight * nlp_influence

    if influence_weight <= 0:
        return None
    return clamp01(weighted_signal / influence_weight)


def _nlp_review_summary(feature_evidence: list[dict[str, object]]) -> str | None:
    backed_rows = [
        row
        for row in feature_evidence
        if _to_float(row.get("nlp_review_score")) is not None
        and (_to_float(row.get("nlp_influence")) or 0) > 0
    ]
    if not backed_rows:
        return None

    ranked = sorted(
        backed_rows,
        key=lambda row: (
            -(
                (_to_float(row.get("preference_weight")) or 0)
                * (_to_float(row.get("nlp_influence")) or 0)
                * (_to_float(row.get("nlp_review_score")) or 0)
            ),
            -(_to_float(row.get("nlp_review_score")) or 0),
        ),
    )
    labels = [
        str(row.get("display_label") or row.get("feature_key")).lower()
        for row in ranked[:2]
    ]
    if len(labels) == 1:
        return f"Review-derived signals mainly reinforce {labels[0]} for this profile."
    return (
        f"Review-derived signals reinforce {labels[0]} and {labels[1]} "
        "for this profile."
    )


def _preference_match_score(
    *,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> float:
    preference_weights: dict[str, float] = {
        str(row["feature_key"]): float(row.get("preference_weight") or 0)
        for row in preference_rows
        if str(row["feature_key"]) in CORE_RECOMMENDATION_FEATURES
    }
    total_weight = sum(preference_weights.values())
    if total_weight <= 0:
        return 0.5

    user_vector = [
        preference_weights.get(feature_key, 0.0)
        for feature_key in CORE_RECOMMENDATION_FEATURES
    ]
    item_raw = [
        clamp01(effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]))
        for feature_key in CORE_RECOMMENDATION_FEATURES
    ]
    item_total = sum(item_raw) or float(len(item_raw))
    item_shape = [value / item_total for value in item_raw]

    priority_weights = [1.0 + (weight * 2.0) for weight in user_vector]
    numerator = sum(
        priority_weights[index] * user_vector[index] * item_shape[index]
        for index in range(len(CORE_RECOMMENDATION_FEATURES))
    )
    denom_left = math.sqrt(
        sum(
            priority_weights[index] * (user_vector[index] ** 2)
            for index in range(len(CORE_RECOMMENDATION_FEATURES))
        )
    )
    denom_right = math.sqrt(
        sum(
            priority_weights[index] * (item_shape[index] ** 2)
            for index in range(len(CORE_RECOMMENDATION_FEATURES))
        )
    )
    shape_similarity = (
        numerator / (denom_left * denom_right)
        if denom_left > 0 and denom_right > 0
        else 0.5
    )

    top_features = sorted(
        preference_weights.items(),
        key=lambda item: item[1],
        reverse=True,
    )[:3]
    top_weight = sum(weight for _, weight in top_features) or 1.0
    top_alignment = (
        sum(
            clamp01(effective_scores.get(feature_key, FEATURE_PRIORS[feature_key]))
            * weight
            for feature_key, weight in top_features
        )
        / top_weight
    )

    return clamp01((shape_similarity * 0.75) + (top_alignment * 0.25))


def _budget_fit_score(price_rm: float | None, budget_tier: str) -> float:
    item_tier = _item_price_tier(price_rm)
    tier_scores = BUDGET_TIER_FIT_SCORES.get(
        budget_tier,
        BUDGET_TIER_FIT_SCORES["between_30_50"],
    )
    return clamp01(tier_scores.get(item_tier, tier_scores["unknown"]))


def _item_price_tier(price_rm: float | None) -> str:
    if price_rm is None:
        return "unknown"
    if price_rm < 30:
        return "low"
    if price_rm <= 50:
        return "mid"
    return "high"


def _rule_fit_score(
    *,
    item: StringItem,
    effective_scores: dict[str, float],
    auxiliary_scores: dict[str, float],
    request: RecommendationRequestModel,
) -> tuple[float, list[str], list[dict[str, object]]]:
    score = 0.55
    reasons: list[str] = []
    events: list[dict[str, object]] = []

    def apply(delta: float, reason: str, rule_key: str) -> None:
        nonlocal score
        score = clamp01(score + delta)
        reasons.append(reason)
        events.append({"rule": rule_key, "delta": round(delta, 4), "reason": reason})

    gauge = item.gauge_main_mm or 0.66
    durability = effective_scores["durability"]
    comfort = effective_scores["comfort"]
    control = effective_scores["control"]
    repulsion = effective_scores["repulsion"]
    elasticity = effective_scores["elasticity"]
    tension_retention = effective_scores["tension_retention"]
    string_movement = effective_scores["string_movement"]
    value_for_money = auxiliary_scores.get("value_for_money", 0.5)

    if request.skill_level == "beginner":
        if gauge <= 0.63:
            apply(
                -0.10,
                "penalizes ultra-thin gauge for beginner consistency",
                "beginner_ultra_thin_penalty",
            )
        if ((comfort + durability) / 2) >= 0.65:
            apply(
                0.06,
                "rewards beginner-friendly comfort and durability",
                "beginner_comfort_durability_bonus",
            )

    if request.frequency_per_week >= 3:
        if durability < 0.50:
            apply(
                -0.08,
                "penalizes low durability for frequent play",
                "frequent_play_low_durability_penalty",
            )
        elif durability >= 0.68:
            apply(
                0.05,
                "supports frequent play with stronger durability",
                "frequent_play_durability_bonus",
            )

    if request.preferred_tension >= 27:
        if tension_retention >= 0.68:
            apply(
                0.06,
                "supports high preferred tension with stronger retention",
                "high_tension_retention_bonus",
            )
        elif tension_retention < 0.55:
            apply(
                -0.06,
                "penalizes lower retention for high preferred tension",
                "high_tension_retention_penalty",
            )

    if request.preferred_tension <= 23 and comfort >= 0.66:
        apply(
            0.04,
            "aligns lower-tension setup with comfort support",
            "low_tension_comfort_bonus",
        )

    if request.playing_style == "attacking":
        attack_support = (repulsion * 0.6) + (elasticity * 0.4)
        if attack_support >= 0.72:
            apply(
                0.07,
                "supports attacking play through repulsion and elasticity",
                "attacking_repulsion_elasticity_bonus",
            )
        elif repulsion < 0.55:
            apply(
                -0.05,
                "penalizes weaker repulsion for attacking style",
                "attacking_low_repulsion_penalty",
            )

    if request.playing_style == "control_defensive":
        control_support = (control * 0.55) + (string_movement * 0.45)
        if control_support >= 0.68:
            apply(
                0.07,
                "supports control style through stable response and movement control",
                "control_stability_bonus",
            )
        elif string_movement < 0.50:
            apply(
                -0.05,
                "penalizes unstable string movement for control style",
                "control_unstable_movement_penalty",
            )

    if request.playing_style == "balanced":
        all_round = (
            repulsion
            + control
            + durability
            + comfort
            + elasticity
            + tension_retention
            + string_movement
        ) / 7
        if all_round >= 0.66:
            apply(
                0.05,
                "rewards balanced all-round response",
                "balanced_all_round_bonus",
            )

    if request.budget_tier == "below_30":
        if value_for_money >= 0.70:
            apply(
                0.05,
                "rewards stronger value-for-money for budget-sensitive preference",
                "below_30_value_bonus",
            )
        elif value_for_money <= 0.45:
            apply(
                -0.06,
                "penalizes weak value-for-money for budget-sensitive preference",
                "below_30_value_penalty",
            )

    return score, reasons, events


def _build_reasons(
    *,
    item: StringItem,
    request: RecommendationRequestModel,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
    budget_fit: float,
    item_price_tier: str,
    confidence_score: float,
    rule_reasons: list[str],
) -> list[str]:
    reasons: list[str] = []

    for feature_key, label in _top_weighted_preference_reasons(
        effective_scores,
        preference_rows,
    ):
        reasons.append(f"matches your {label} priority")

    tier_label = PRICE_TIER_LABELS.get(item_price_tier, PRICE_TIER_LABELS["unknown"])
    if budget_fit >= 0.9 and item.price_rm is not None:
        reasons.append(f"{tier_label} strongly fits your budget tier")
    elif budget_fit >= 0.7 and item.price_rm is not None:
        reasons.append(f"{tier_label} is acceptable for your budget tier")
    elif item.price_rm is not None:
        reasons.append(f"{tier_label} is a budget trade-off")

    reasons.extend(rule_reasons)

    if confidence_score >= 0.75:
        reasons.append("supported by stronger official and review evidence")
    elif confidence_score <= 0.45:
        reasons.append("uses partial evidence, suitable as an exploratory option")

    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.75:
        reasons.append("strong repulsion response for attacking rallies")
    if (
        request.playing_style == "control_defensive"
        and effective_scores["control"] >= 0.75
    ):
        reasons.append("control-oriented response for placement and touch")

    return _unique(reasons)[:4]


def _top_weighted_preference_reasons(
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> list[tuple[str, str]]:
    ranked = []
    for row in preference_rows:
        feature_key = str(row["feature_key"])
        if feature_key not in CORE_RECOMMENDATION_FEATURES:
            continue
        weight = float(row.get("preference_weight") or 0)
        ranked.append((weight * effective_scores.get(feature_key, 0.5), feature_key))
    ranked.sort(reverse=True)
    return [(feature_key, FEATURE_LABELS[feature_key]) for _, feature_key in ranked[:2]]


def _primary_fit_angle(
    effective_scores: dict[str, float],
    auxiliary_scores: dict[str, float],
    request: RecommendationRequestModel,
    *,
    budget_fit: float,
    confidence_score: float,
) -> str:
    if (
        request.budget_tier == "below_30"
        and budget_fit >= 0.9
        and auxiliary_scores.get("value_for_money", 0.5) >= 0.7
    ):
        return "Budget-safe pick"
    if confidence_score <= 0.45:
        return "Exploratory pick"
    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.7:
        return "Attack pick"
    if (
        request.playing_style == "control_defensive"
        and effective_scores["control"] >= 0.7
    ):
        return "Control pick"

    ranked = sorted(
        (
            ("Durability pick", effective_scores["durability"]),
            ("Comfort pick", effective_scores["comfort"]),
            ("Elastic pick", effective_scores["elasticity"]),
            ("Tension-safe pick", effective_scores["tension_retention"]),
            ("Stable-bed pick", effective_scores["string_movement"]),
            ("Sound pick", effective_scores["sound"]),
            ("All-round pick", sum(effective_scores.values()) / len(effective_scores)),
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0][0]


def _trade_off_summary(
    effective_scores: dict[str, float],
    breakdown: dict[str, float],
    request: RecommendationRequestModel,
) -> str:
    weakest_component = min(
        (
            ("preference match", breakdown["preference_match"]),
            ("rule fit", breakdown["rule_fit"]),
            ("budget fit", breakdown["budget_fit"]),
            ("confidence", breakdown.get("confidence_score", 0.5)),
        ),
        key=lambda item: item[1],
    )[0]

    if weakest_component == "budget fit":
        return "Budget tier alignment is the main trade-off for this option."
    if weakest_component == "confidence":
        return "Evidence confidence is lower because feature support is sparse."
    if weakest_component == "rule fit":
        return (
            "Domain-rule support is moderate here for your "
            f"{request.playing_style.replace('_', ' ')} profile."
        )

    weakest_feature = min(effective_scores.items(), key=lambda item: item[1])[0]
    return (
        f"Lower {weakest_feature.replace('_', ' ')} is the main performance trade-off."
    )


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _signal_score(value: object) -> float | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return clamp01(value.normalized_score)
    score = _to_float(value)
    return clamp01(score) if score is not None else None


def _signal_confidence(value: object) -> float | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return clamp01(value.confidence) if value.confidence is not None else None
    return None


def _signal_source_version(value: object) -> str | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return value.source_version
    return None


def _signal_source_ref(value: object) -> str | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return value.source_ref
    return None


def _signal_review_count_snapshot(value: object) -> int | None:
    if isinstance(value, RecommendationFeatureSignalModel):
        return value.review_count_snapshot
    return None


def _review_count_confidence(review_count: int) -> float:
    if review_count <= 0:
        return 0.0
    return clamp01(math.log1p(review_count) / math.log1p(1000))


def _to_float(value: object) -> float | None:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
