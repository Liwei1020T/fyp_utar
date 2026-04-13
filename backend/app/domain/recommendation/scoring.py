from __future__ import annotations

from dataclasses import dataclass

from app.domain.catalog.entities import StringItem
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResultModel


ALGORITHM_VERSION = "fyp1_preference_official_nlp_rule_budget_v3"
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


@dataclass(frozen=True)
class ScoredRecommendation:
    result: RecommendationResultModel
    cache_payload: dict[str, object]
    preference_vector_rows: list[dict[str, float | str | None]]


class Fyp1ContentRecommendationScorer:
    """Rule-enhanced content scorer; no collaborative filtering is used in FYP1."""

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
            effective_scores, feature_sources = _effective_item_features(candidate)
            feature_evidence = _build_feature_evidence(
                candidate=candidate,
                effective_scores=effective_scores,
                feature_sources=feature_sources,
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
            budget_fit = _budget_fit_score(
                candidate.item.price_rm,
                request,
            )
            rule_fit, rule_reasons, rule_events = _rule_fit_score(
                item=candidate.item,
                effective_scores=effective_scores,
                auxiliary_scores=auxiliary_scores,
                request=request,
            )
            final_score = round(
                clamp01(
                    (preference_match * 0.60) + (rule_fit * 0.25) + (budget_fit * 0.15)
                ),
                4,
            )

            reasons = _build_reasons(
                item=candidate.item,
                request=request,
                effective_scores=effective_scores,
                preference_rows=preference_vector_rows,
                budget_fit=budget_fit,
                rule_reasons=rule_reasons,
            )
            breakdown = {
                "preference_match": round(preference_match, 4),
                "rule_fit": round(rule_fit, 4),
                "budget_fit": round(budget_fit, 4),
                "final_score": final_score,
            }
            if nlp_review_score is not None:
                breakdown["nlp_review_score"] = round(nlp_review_score, 4)
            fit_angle = _primary_fit_angle(effective_scores, auxiliary_scores, request)
            rationale_payload = {
                "catalog_id": candidate.item.id,
                "display_name": candidate.item.display_name,
                "brand": candidate.item.brand,
                "model_name": candidate.item.model_name,
                "algorithm_family": ("rule_enhanced_content_based_official_nlp_budget"),
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
                    key: round(value, 4)
                    for key, value in candidate.matrix_by_source.get(
                        "nlp_review", {}
                    ).items()
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
                    "budget_min": request.budget_min,
                    "budget_max": request.budget_max,
                },
                "rule_events": rule_events,
                "profile_context": {
                    "skill_level": request.skill_level,
                    "playing_style": request.playing_style,
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
                    feature_key: round(effective_scores.get(feature_key, 0.5), 4)
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
                        "nlp_review_score": breakdown.get("nlp_review_score"),
                        "final_score": final_score,
                        "rank_position": 0,
                        "rationale": rationale_payload,
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
) -> tuple[dict[str, float], dict[str, str]]:
    official_scores = _official_feature_scores(candidate.item)
    nlp_scores = candidate.matrix_by_source.get("nlp_review", {})

    effective: dict[str, float] = {}
    sources: dict[str, str] = {}
    for feature_key in CORE_RECOMMENDATION_FEATURES:
        official_value = official_scores.get(feature_key)
        nlp_value = _nlp_feature_score(nlp_scores, feature_key)
        if official_value is not None and nlp_value is not None:
            effective[feature_key] = clamp01(
                (official_value * 0.65) + (nlp_value * 0.35)
            )
            sources[feature_key] = "official_performance+nlp_review"
        elif official_value is not None:
            effective[feature_key] = clamp01(official_value)
            sources[feature_key] = "official_performance"
        elif nlp_value is not None:
            effective[feature_key] = clamp01(nlp_value)
            sources[feature_key] = "nlp_review"
        else:
            effective[feature_key] = 0.5
            sources[feature_key] = "neutral_fallback"
    return effective, sources


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


def _nlp_feature_score(nlp_scores: dict[str, float], feature_key: str) -> float | None:
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
                scores[feature_key] = value
    return scores


def _build_feature_evidence(
    *,
    candidate: RecommendationCandidateModel,
    effective_scores: dict[str, float],
    feature_sources: dict[str, str],
    preference_rows: list[dict[str, float | str | None]],
) -> list[dict[str, object]]:
    official_scores = _official_feature_scores(candidate.item)
    nlp_scores = candidate.matrix_by_source.get("nlp_review", {})
    preference_weights = {
        str(row["feature_key"]): round(float(row.get("preference_weight") or 0), 4)
        for row in preference_rows
    }
    rows: list[dict[str, object]] = []

    for feature_key in CORE_RECOMMENDATION_FEATURES:
        source = feature_sources.get(feature_key, "neutral_fallback")
        nlp_influence = 0.0
        if source == "official_performance+nlp_review":
            nlp_influence = 0.35
        elif source == "nlp_review":
            nlp_influence = 1.0

        official_score = official_scores.get(feature_key)
        nlp_score = _nlp_feature_score(nlp_scores, feature_key)
        rows.append(
            {
                "feature_key": feature_key,
                "display_label": FEATURE_LABELS[feature_key].title(),
                "effective_score": round(effective_scores.get(feature_key, 0.5), 4),
                "preference_weight": preference_weights.get(feature_key, 0.0),
                "source": source,
                "official_score": round(official_score, 4)
                if official_score is not None
                else None,
                "nlp_review_score": round(nlp_score, 4)
                if nlp_score is not None
                else None,
                "nlp_influence": round(nlp_influence, 4),
            }
        )

    rows.sort(
        key=lambda row: (
            -(_to_float(row.get("preference_weight")) or 0)
            * (_to_float(row.get("effective_score")) or 0),
            -(_to_float(row.get("effective_score")) or 0),
        )
    )
    return rows


def _nlp_review_alignment_score(
    *,
    feature_evidence: list[dict[str, object]],
    preference_rows: list[dict[str, float | str | None]],
) -> float | None:
    total_primary_weight = sum(
        float(row.get("preference_weight") or 0)
        for row in preference_rows
        if str(row["feature_key"]) in CORE_RECOMMENDATION_FEATURES
    )
    if total_primary_weight <= 0:
        return None

    weighted_total = 0.0
    has_nlp_signal = False
    for row in feature_evidence:
        nlp_score = _to_float(row.get("nlp_review_score"))
        nlp_influence = _to_float(row.get("nlp_influence")) or 0
        if nlp_score is None or nlp_influence <= 0:
            continue
        has_nlp_signal = True
        weighted_total += (
            nlp_score * (_to_float(row.get("preference_weight")) or 0) * nlp_influence
        )

    if not has_nlp_signal:
        return None
    return clamp01(weighted_total / total_primary_weight)


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
            -(_to_float(row.get("preference_weight")) or 0)
            * (_to_float(row.get("nlp_influence")) or 0)
            * (_to_float(row.get("nlp_review_score")) or 0),
            -(_to_float(row.get("nlp_review_score")) or 0),
        ),
    )
    labels = [
        str(row.get("display_label") or row.get("feature_key")) for row in ranked[:2]
    ]
    if len(labels) == 1:
        return f"Review-derived signals mainly reinforce {labels[0].lower()} for this profile."
    return (
        f"Review-derived signals reinforce {labels[0].lower()} and {labels[1].lower()} "
        "for this profile."
    )


def _preference_match_score(
    *,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
) -> float:
    weighted_total = 0.0
    total_weight = 0.0
    for row in preference_rows:
        feature_key = str(row["feature_key"])
        weight = float(row.get("preference_weight") or 0)
        if feature_key in CORE_RECOMMENDATION_FEATURES:
            weighted_total += effective_scores.get(feature_key, 0.5) * weight
            total_weight += weight
    if total_weight == 0:
        return 0.5
    return clamp01(weighted_total / total_weight)


def _budget_fit_score(
    price_rm: float | None,
    request: RecommendationRequestModel,
) -> float:
    if price_rm is None:
        return 0.5
    budget_min = request.budget_min
    budget_max = request.budget_max
    if budget_min <= price_rm <= budget_max:
        span = max(budget_max - budget_min, 10)
        midpoint = (budget_min + budget_max) / 2
        closeness = 1 - min(abs(price_rm - midpoint) / span, 1)
        return clamp01(max(0.8, closeness))

    span = max(budget_max - budget_min, 10)
    if price_rm < budget_min:
        # budget_min is a soft preference: cheaper strings should lose only a little fit.
        gap = budget_min - price_rm
        return clamp01(0.8 - min(0.18, gap / (span * 4)))

    # budget_max is the stronger ceiling for FYP1 business logic.
    gap = price_rm - budget_max
    return clamp01(0.8 - min(0.65, gap / span))


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

    durability = effective_scores["durability"]
    comfort = effective_scores["comfort"]
    control = effective_scores["control"]
    repulsion = effective_scores["repulsion"]
    sound = effective_scores["sound"]
    value_for_money = auxiliary_scores.get("value_for_money", 0.5)
    elasticity = effective_scores["elasticity"]
    tension_retention = effective_scores["tension_retention"]
    string_movement = effective_scores["string_movement"]

    if request.skill_level == "beginner" and (item.gauge_main_mm or 0.66) <= 0.63:
        apply(
            -0.18,
            "penalizes an ultra-thin gauge for beginner play",
            "beginner_thin_gauge_penalty",
        )
    if request.skill_level == "beginner" and (comfort + durability) / 2 >= 0.68:
        apply(
            0.10,
            "rewards beginner-friendly comfort and durability",
            "beginner_comfort_durability_bonus",
        )

    if (
        request.playing_style == "attacking"
        and (item.gauge_main_mm or 0.66) <= 0.66
        and repulsion >= 0.68
    ):
        apply(
            0.12,
            "rewards an attacking setup with thinner gauge and strong repulsion",
            "attacking_thin_repulsion_bonus",
        )
    if request.playing_style == "control_defensive" and control >= 0.68:
        apply(0.12, "fits your control-oriented playing style", "control_bonus")
    if (
        request.playing_style == "balanced"
        and (
            repulsion
            + control
            + durability
            + comfort
            + elasticity
            + tension_retention
            + string_movement
        )
        / 7
        >= 0.64
    ):
        apply(0.08, "offers a balanced all-round response", "balanced_bonus")

    if request.frequency_per_week >= 3 and durability < 0.55:
        apply(
            -0.12,
            "penalizes lower durability for frequent play",
            "frequent_play_durability_penalty",
        )
    elif request.frequency_per_week >= 3 and durability >= 0.68:
        apply(
            0.08,
            "supports frequent play with stronger durability",
            "frequent_play_durability_bonus",
        )

    value_priority = request.pref_value_for_money / 10
    if value_priority >= 0.6 and value_for_money >= 0.68:
        apply(
            0.05,
            "rewards value-for-money because it matters in your profile",
            "value_priority_bonus",
        )
    if request.budget_max <= 40 and value_for_money <= 0.45:
        apply(
            -0.08,
            "penalizes weak value-for-money for a tighter budget",
            "low_budget_value_penalty",
        )
    if request.budget_max <= 40 and value_for_money >= 0.70:
        apply(
            0.06,
            "rewards better value-for-money for a tighter budget",
            "low_budget_value_bonus",
        )

    if request.preferred_tension >= 27 and (item.gauge_main_mm or 0.66) >= 0.67:
        apply(
            0.06,
            "aligns with your higher preferred tension",
            "high_tension_gauge_bonus",
        )
    if request.preferred_tension >= 27 and tension_retention >= 0.68:
        apply(
            0.06,
            "supports higher tension with stronger tension retention",
            "high_tension_retention_bonus",
        )
    if request.preferred_tension <= 23 and comfort >= 0.65:
        apply(
            0.05,
            "aligns with your lower-tension comfort preference",
            "low_tension_comfort_bonus",
        )
    if request.playing_style == "attacking" and elasticity >= 0.70:
        apply(
            0.05,
            "adds elastic rebound support for attacking play",
            "attacking_elasticity_bonus",
        )
    if request.playing_style == "control_defensive" and string_movement >= 0.65:
        apply(
            0.05,
            "supports control with more stable string movement",
            "control_string_movement_bonus",
        )
    if request.playing_style == "attacking" and sound >= 0.72:
        apply(
            0.04, "adds a crisp sound cue for attacking play", "attacking_sound_bonus"
        )

    return score, reasons, events


def _build_reasons(
    *,
    item: StringItem,
    request: RecommendationRequestModel,
    effective_scores: dict[str, float],
    preference_rows: list[dict[str, float | str | None]],
    budget_fit: float,
    rule_reasons: list[str],
) -> list[str]:
    reasons: list[str] = []
    for feature_key, label in _top_weighted_preference_reasons(
        effective_scores,
        preference_rows,
    ):
        reasons.append(f"matches your {label} preference")
    if budget_fit >= 0.8 and item.price_rm is not None:
        reasons.append("within your budget range")
    elif budget_fit >= 0.55 and item.price_rm is not None:
        reasons.append("close to your budget range")
    reasons.extend(rule_reasons)
    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.75:
        reasons.append("strong repulsion and response for attacking rallies")
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
) -> str:
    if request.budget_max <= 40 and auxiliary_scores.get("value_for_money", 0.5) >= 0.7:
        return "Budget-safe pick"
    if request.playing_style == "attacking" and effective_scores["repulsion"] >= 0.68:
        return "Attack pick"
    if (
        request.playing_style == "control_defensive"
        and effective_scores["control"] >= 0.68
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
        ),
        key=lambda item: item[1],
    )[0]
    if weakest_component == "budget fit":
        return "Budget alignment is the main trade-off for this option."
    weakest_feature = min(effective_scores.items(), key=lambda item: item[1])[0]
    if weakest_component == "rule fit":
        return f"Domain rules are less decisive here, especially for your {request.playing_style.replace('_', ' ')} style."
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
