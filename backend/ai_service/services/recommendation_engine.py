from __future__ import annotations

from math import inf

from ai_service.schemas.recommendation import BudgetRange
from ai_service.schemas.recommendation import ExplainRequest
from ai_service.schemas.recommendation import ExplainResponse
from ai_service.schemas.recommendation import RecommendRequest
from ai_service.schemas.recommendation import RecommendResponse
from ai_service.schemas.recommendation import RecommendationContext
from ai_service.schemas.recommendation import RecommendationResultItem
from ai_service.schemas.recommendation import StringCandidate

ALGORITHM_VERSION = "fyp1-rule-based-content-v4"


def generate_recommendations(payload: RecommendRequest) -> RecommendResponse:
    effective_context = merge_context(payload.profile, payload.request)
    candidates, fallback_reason = filter_candidates(payload.catalog, effective_context)

    results = [
        build_result(
            item,
            context=effective_context,
            fallback_reason=fallback_reason,
        )
        for item in candidates
    ]
    results.sort(
        key=lambda item: (
            -item.match_score,
            item.price if item.price is not None else inf,
            item.brand,
            item.model_name,
        )
    )
    ranked = [
        RecommendationResultItem(
            **{
                **item.model_dump(),
                "rank": rank,
            }
        )
        for rank, item in enumerate(results[: payload.top_k], start=1)
    ]
    return RecommendResponse(
        algorithm_version=ALGORITHM_VERSION,
        evaluated_candidates=len(candidates),
        results=ranked,
    )


def explain_recommendation(payload: ExplainRequest) -> ExplainResponse:
    effective_context = merge_context(payload.profile, payload.request)
    score, reasons = score_item(payload.string, effective_context)
    evidence = reasons[:5] if reasons else ["baseline catalog fit"]
    summary = (
        f"{payload.string.brand} {payload.string.model_name} scored {score:.2f} "
        f"for this player because it aligns with {', '.join(evidence[:3])}."
    )
    return ExplainResponse(
        algorithm_version=ALGORITHM_VERSION,
        summary=summary,
        evidence=evidence,
        key_strengths=key_strengths_for(payload.string),
    )


def merge_context(
    profile: RecommendationContext,
    request: RecommendationContext,
) -> RecommendationContext:
    data = profile.model_dump(exclude_none=True)
    data.update(request.model_dump(exclude_none=True))
    return RecommendationContext(**data)


def filter_candidates(
    catalog: list[StringCandidate],
    context: RecommendationContext,
) -> tuple[list[StringCandidate], str | None]:
    budget_matches = [item for item in catalog if matches_budget(item, context.budget)]
    tension_matches = [
        item
        for item in budget_matches
        if matches_tension(item, context.preferred_tension)
    ]
    if tension_matches:
        return tension_matches, None
    if budget_matches:
        return budget_matches, "closest tension match available in the current catalog"
    return catalog, "closest active catalog match available for the current budget"


def matches_budget(item: StringCandidate, budget: BudgetRange | None) -> bool:
    if item.price is None or budget is None:
        return True
    if budget.min is not None and item.price < budget.min:
        return False
    if budget.max is not None and item.price > budget.max:
        return False
    return True


def matches_tension(item: StringCandidate, preferred_tension: float | None) -> bool:
    if preferred_tension is None:
        return True
    low = item.recommended_tension_min or 20
    high = item.recommended_tension_max or 28
    return low <= preferred_tension <= high


def key_strengths_for(item: StringCandidate) -> list[str]:
    aspect_scores = {
        "repulsion": item.repulsion_score or 0,
        "durability": item.durability_score or 0,
        "control": item.control_score or 0,
        "sound": item.sound_score or 0,
        "tension_retention": item.tension_retention_score or 0,
    }
    ranked = sorted(aspect_scores.items(), key=lambda entry: entry[1], reverse=True)
    strengths = [name for name, value in ranked if value > 0]
    return strengths[:3] if strengths else ["balanced fit"]


def short_reason(reasons: list[str]) -> str:
    if reasons:
        return f"Matches your profile through {', '.join(reasons[:3])}."
    return "Matches your current balance of control, durability, and tension stability."


def build_result(
    item: StringCandidate,
    *,
    context: RecommendationContext,
    fallback_reason: str | None,
) -> RecommendationResultItem:
    score, reasons = score_item(item, context)
    if fallback_reason is not None:
        reasons.insert(0, fallback_reason)
    low = item.recommended_tension_min or 20
    high = item.recommended_tension_max or 28
    return RecommendationResultItem(
        rank=0,
        id=item.id,
        string_id=item.id,
        brand=item.brand,
        model_name=item.model_name,
        match_score=round(score, 2),
        short_reason=short_reason(reasons),
        price=item.price,
        key_strengths=key_strengths_for(item),
        suggested_tension_range=f"{low}-{high} lbs",
    )


def score_item(
    item: StringCandidate,
    context: RecommendationContext,
) -> tuple[float, list[str]]:
    score = 20.0
    contributions: list[tuple[str, float]] = []

    if context.preferred_tension is not None and matches_tension(
        item, context.preferred_tension
    ):
        contributions.append(("tension range fit", 6.0))

    priority_fields = (
        ("control_priority", item.control_score, "control support"),
        ("repulsion_priority", item.repulsion_score, "repulsion support"),
        ("durability_priority", item.durability_score, "durability support"),
        ("sound_priority", item.sound_score, "hitting sound preference"),
        (
            "tension_retention_priority",
            item.tension_retention_score,
            "tension stability",
        ),
    )
    for field_name, item_score, label in priority_fields:
        priority = getattr(context, field_name)
        if priority is None or item_score is None:
            continue
        contributions.append((label, float(priority) * float(item_score)))

    if context.playing_style == "control":
        contributions.append(
            (
                "control-oriented style",
                (item.control_score or 0) * 1.4
                + (item.tension_retention_score or 0) * 0.6,
            )
        )
    elif context.playing_style == "defensive":
        contributions.append(
            (
                "defensive consistency",
                (item.control_score or 0) * 0.8
                + (item.durability_score or 0)
                + (item.tension_retention_score or 0) * 0.6,
            )
        )
    elif context.playing_style == "attacking":
        contributions.append(
            (
                "attacking response",
                (item.repulsion_score or 0) * 1.5 + (item.sound_score or 0) * 0.8,
            )
        )
    elif context.playing_style == "balanced":
        contributions.append(
            (
                "balanced all-round fit",
                (item.control_score or 0)
                + (item.repulsion_score or 0)
                + (item.durability_score or 0),
            )
        )

    if context.skill_level == "beginner":
        contributions.append(
            (
                "beginner-friendly value",
                (item.value_score or 0) * 0.8 + (item.durability_score or 0) * 0.4,
            )
        )
    elif context.skill_level == "advanced":
        contributions.append(
            (
                "advanced response",
                (item.control_score or 0) * 0.7 + (item.repulsion_score or 0) * 0.7,
            )
        )

    if context.budget is not None and item.price is not None:
        midpoint = budget_midpoint(context.budget)
        if midpoint is not None:
            distance = abs(item.price - midpoint)
            contributions.append(("budget fit", max(0.0, 3.0 - distance / 5.0)))

    score += sum(value for _, value in contributions if value > 0)
    contributions.sort(key=lambda item: item[1], reverse=True)
    reasons = [label for label, value in contributions if value > 0]
    return score, list(dict.fromkeys(reasons))


def budget_midpoint(budget: BudgetRange) -> float | None:
    if budget.min is not None and budget.max is not None:
        return (budget.min + budget.max) / 2
    if budget.max is not None:
        return budget.max
    if budget.min is not None:
        return budget.min
    return None
