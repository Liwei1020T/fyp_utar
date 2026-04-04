from __future__ import annotations

from ai_service.schemas.review_analysis import ReviewAnalysisRequest
from ai_service.schemas.review_analysis import ReviewAnalysisResponse
from ai_service.schemas.review_analysis import ReviewAspectSummary

ASPECT_KEYWORDS: dict[str, tuple[list[str], list[str]]] = {
    "repulsion": (["repulsion", "elastic", "弹性"], ["dull", "dead"]),
    "durability": (["durable", "耐打", "lasts"], ["break", "fragile"]),
    "control": (["control", "控球"], ["wild", "slippery"]),
    "sound": (["sound", "crispy", "清脆"], ["muted", "flat"]),
    "tension_retention": (
        ["retention", "掉磅", "stable"],
        ["lost tension", "drop fast"],
    ),
}


def analyze_reviews(payload: ReviewAnalysisRequest) -> ReviewAnalysisResponse:
    extracted: list[ReviewAspectSummary] = []
    combined_text = " ".join(review.review_text.lower() for review in payload.reviews)

    for aspect, (positive_keywords, negative_keywords) in ASPECT_KEYWORDS.items():
        positive_hits = [
            keyword for keyword in positive_keywords if keyword.lower() in combined_text
        ]
        negative_hits = [
            keyword for keyword in negative_keywords if keyword.lower() in combined_text
        ]
        if not positive_hits and not negative_hits:
            continue

        sentiment = (
            "positive" if len(positive_hits) >= len(negative_hits) else "negative"
        )
        evidence = positive_hits + negative_hits
        confidence = min(0.95, 0.45 + len(evidence) * 0.1)
        extracted.append(
            ReviewAspectSummary(
                aspect=aspect,
                sentiment=sentiment,
                confidence=round(confidence, 2),
                evidence=evidence[:4],
            )
        )

    if not extracted:
        summary = "No strong aspect signals were detected in the provided reviews."
    else:
        summary = "Detected review signals for " + ", ".join(
            f"{item.aspect} ({item.sentiment})" for item in extracted
        )

    return ReviewAnalysisResponse(
        review_count=len(payload.reviews),
        extracted_aspects=extracted,
        summary=summary,
    )
