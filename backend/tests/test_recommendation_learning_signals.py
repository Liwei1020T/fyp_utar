from __future__ import annotations

from datetime import datetime
from datetime import timezone

import pytest

from app.domain.recommendation.entities import FeedbackRow
from app.domain.recommendation.entities import RecommendationInteraction
from app.domain.recommendation.learning_signals import build_cf_evidence
from app.domain.recommendation.learning_signals import build_feedback_snapshot
from app.domain.recommendation.learning_signals import canonical_racket_model_key
from app.domain.recommendation.learning_signals import cf_weight_for_support
from app.domain.recommendation.learning_signals import normalize_racket_model_key
from app.domain.recommendation.learning_signals import STANDARD_RACKET_MODELS


NOW = datetime(2026, 8, 13, tzinfo=timezone.utc)
MODEL_KEY = "yonex:astrox 88d pro"


def test_racket_key_normalizes_identity_without_fuzzy_matching() -> None:
    assert normalize_racket_model_key(" YONEX ", "Astrox-88D  Pro") == MODEL_KEY
    assert normalize_racket_model_key("Yonex", "Astrox 88D") != MODEL_KEY
    assert normalize_racket_model_key("Yonex", None) is None
    assert canonical_racket_model_key(" YONEX ", "Astrox-88D  Pro") == MODEL_KEY
    assert canonical_racket_model_key("Yonex", "Astrox 88D") is None
    assert all(
        normalize_racket_model_key(brand, model) == key
        for key, brand, model in STANDARD_RACKET_MODELS
    )


def test_feedback_uses_exact_context_then_global_and_averages_each_user() -> None:
    rows = [
        _feedback("f1", "u1", 5, MODEL_KEY),
        _feedback("f2", "u1", 1, MODEL_KEY),
        _feedback("f3", "u2", 5, MODEL_KEY),
        _feedback("f4", "u3", 1, "victor:thruster k"),
    ]

    exact = build_feedback_snapshot(rows, target_racket_model_key=MODEL_KEY)
    control = exact.by_catalog["yonex-bg80"]["control"]
    assert control.evidence_scope == "exact_racket_model"
    assert control.distinct_users == 2
    assert control.booking_count == 3
    assert control.normalized_score == pytest.approx(0.75)
    assert control.weight == pytest.approx(0.05)

    global_only = build_feedback_snapshot(rows, target_racket_model_key=None)
    global_control = global_only.by_catalog["yonex-bg80"]["control"]
    assert global_control.evidence_scope == "global_string"
    assert global_control.distinct_users == 3
    assert global_control.booking_count == 4
    assert global_control.normalized_score == pytest.approx(0.5)


def test_feedback_source_version_changes_when_rating_changes() -> None:
    first = build_feedback_snapshot(
        [_feedback("f1", "u1", 2, MODEL_KEY)],
        target_racket_model_key=MODEL_KEY,
    )
    changed = build_feedback_snapshot(
        [_feedback("f1", "u1", 5, MODEL_KEY)],
        target_racket_model_key=MODEL_KEY,
    )

    assert (
        first.by_catalog["yonex-bg80"]["control"].source_version
        != changed.by_catalog["yonex-bg80"]["control"].source_version
    )
    assert first.snapshot_version != changed.snapshot_version


def test_custom_racket_feedback_uses_global_scope() -> None:
    snapshot = build_feedback_snapshot(
        [_feedback("f1", "u1", 5, None)],
        target_racket_model_key=None,
    )

    aggregate = snapshot.by_catalog["yonex-bg80"]["control"]
    assert aggregate.evidence_scope == "global_string"
    assert aggregate.racket_model_key is None


def test_feedback_snapshot_version_does_not_depend_on_query_order() -> None:
    rows = [
        _feedback("f1", "u1", 2, MODEL_KEY),
        _feedback("f2", "u2", 5, MODEL_KEY),
    ]

    forward = build_feedback_snapshot(rows, target_racket_model_key=MODEL_KEY)
    reversed_rows = build_feedback_snapshot(
        reversed(rows),
        target_racket_model_key=MODEL_KEY,
    )

    assert forward.snapshot_version == reversed_rows.snapshot_version
    assert (
        forward.by_catalog["yonex-bg80"]["control"].source_version
        == reversed_rows.by_catalog["yonex-bg80"]["control"].source_version
    )


def test_cf_evidence_requires_exact_model_peer() -> None:
    interactions = [
        _interaction("b1", "current", "yonex-bg65", MODEL_KEY, 26),
        _interaction("b2", "peer-1", "yonex-bg80", MODEL_KEY, 26),
        _interaction("b3", "peer-1", "yonex-bg80", MODEL_KEY, 24),
        _interaction("b4", "peer-2", "yonex-bg65", "yonex:astrox 88d", 26),
    ]

    evidence = build_cf_evidence(
        interactions,
        current_user_id="current",
        current_preference_vector=(8, 6, 7, 5, 6, 5, 4, 6, 5),
        target_racket_model_key=MODEL_KEY,
        target_tension=26,
    )

    assert evidence.eligible_peer_count == 1
    assert evidence.supporting_users_by_catalog == {"yonex-bg80": 1}
    assert evidence.score_by_catalog["yonex-bg80"] == pytest.approx(0.75)
    assert "yonex-bg65" not in evidence.score_by_catalog


def test_cf_keeps_missing_tension_peers_in_denominator_without_support() -> None:
    interactions = [
        _interaction("b1", "peer-missing-tension", "yonex-bg80", MODEL_KEY, None),
        _interaction("b2", "peer-supported-1", "yonex-bg80", MODEL_KEY, 26),
        _interaction("b3", "peer-supported-2", "yonex-bg80", MODEL_KEY, 26),
    ]

    evidence = build_cf_evidence(
        interactions,
        current_user_id="current",
        current_preference_vector=(8, 6, 7, 5, 6, 5, 4, 6, 5),
        target_racket_model_key=MODEL_KEY,
        target_tension=26,
    )

    assert evidence.eligible_peer_count == 3
    assert evidence.supporting_users_by_catalog == {"yonex-bg80": 2}
    assert evidence.score_by_catalog["yonex-bg80"] == pytest.approx(0.6667)


def test_cf_weight_requires_three_distinct_supporting_users_and_is_bounded() -> None:
    assert cf_weight_for_support(0) == 0
    assert cf_weight_for_support(2) == 0
    assert cf_weight_for_support(3) == pytest.approx(0.0462)
    assert cf_weight_for_support(1_000_000) <= 0.20


def _feedback(
    feedback_id: str,
    user_id: str,
    control: int,
    model_key: str | None,
) -> FeedbackRow:
    return FeedbackRow(
        feedback_id=feedback_id,
        user_id=user_id,
        catalog_id="yonex-bg80",
        racket_model_key=model_key,
        ratings={"control": control},
    )


def _interaction(
    booking_id: str,
    user_id: str,
    catalog_id: str,
    model_key: str,
    tension: float | None,
) -> RecommendationInteraction:
    return RecommendationInteraction(
        booking_id=booking_id,
        user_id=user_id,
        catalog_id=catalog_id,
        racket_id=None,
        racket_model_key=model_key,
        requested_tension=tension,
        completed_at=NOW,
        preference_vector=(8, 6, 7, 5, 6, 5, 4, 6, 5),
    )
