from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

import pytest
from pydantic import ValidationError

from app.domain.profile.entities import PlayerProfile
from app.domain.catalog.entities import InventorySnapshot
from app.domain.catalog.entities import StringItem
from app.domain.catalog.entities import StringOfficialPerformance
from app.domain.catalog.recommendation_features import (
    RECOMMENDATION_FEATURE_DEFINITIONS,
)
from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import CollaborativeEvidence
from app.domain.recommendation.entities import CommunityFeatureAggregate
from app.domain.recommendation.entities import CommunitySnapshot
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.entities import RecommendationResultModel
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.dto.profile import ProfilePayload
from app.dto.recommendation import RecommendationRequestDto
from app.shared.errors import NotFoundError
from app.shared.pagination import Page
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)
from app.use_cases.profile.upsert_my_profile import UpsertMyProfileUseCase


class FakeProfileRepository:
    def __init__(self, profile: PlayerProfile | None = None) -> None:
        self.profile = profile

    def get_by_user_id(self, user_id: str):  # pragma: no cover - not used here
        if self.profile is not None:
            return self.profile
        raise AssertionError("profile lookup should not be used for preview requests")

    def upsert(
        self,
        profile,
        *,
        username=None,
    ):
        self.profile = profile
        return profile


class FakeRecommendationRepository:
    def __init__(
        self,
        candidates: list[RecommendationCandidateModel] | None = None,
    ) -> None:
        self.preference_entries: list[dict[str, float | str | None]] = []
        self.cached: list[CachedRecommendationRecord] = []
        self.cleared_cache_user_ids: list[str] = []
        self.last_cache_algorithm_version: str | None = None
        self._candidates = candidates

    def list_active_candidates(self) -> list[RecommendationCandidateModel]:
        if self._candidates is not None:
            return self._candidates
        return [
            _candidate(
                id="yonex-bg80",
                display_name="Yonex BG80",
                model_name="BG80",
                price_rm=45,
                gauge_main_mm=0.68,
                nlp_scores={
                    "attack": 0.92,
                    "comfort": 0.42,
                    "control": 0.71,
                    "durability": 0.61,
                    "elasticity": 0.88,
                    "sound": 0.86,
                    "string_movement": 0.65,
                    "tension_retention": 0.62,
                    "value_for_money": 0.58,
                },
            ),
            _candidate(
                id="yonex-bg65",
                display_name="Yonex BG65",
                model_name="BG65",
                price_rm=43,
                gauge_main_mm=0.70,
                nlp_scores={
                    "attack": 0.51,
                    "comfort": 0.76,
                    "control": 0.67,
                    "durability": 0.89,
                    "elasticity": 0.45,
                    "sound": 0.41,
                    "string_movement": 0.72,
                    "tension_retention": 0.80,
                    "value_for_money": 0.82,
                },
            ),
        ]

    def get_owned_racket_context(
        self,
        *,
        user_id: str,
        racket_id: str,
        target_tension: float,
    ):
        return None

    def list_community_feedback_rows(self):
        return []

    def list_recommendation_interactions(self):
        return []

    def replace_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str,
        entries: list[dict[str, float | str | None]],
    ):
        assert user_id == "user-1"
        assert source_layer == PREFERENCE_SOURCE_LAYER
        self.preference_entries = entries
        return []

    def list_user_preference_vector(
        self,
        *,
        user_id: str,
        source_layer: str | None = None,
    ):
        raise NotImplementedError

    def replace_score_cache(
        self,
        *,
        user_id: str,
        algorithm_version: str,
        results: list[dict[str, object]],
    ) -> list[CachedRecommendationRecord]:
        assert user_id == "user-1"
        assert algorithm_version == ALGORITHM_VERSION
        self.cached = [
            CachedRecommendationRecord(
                user_id=user_id,
                catalog_id=str(item["catalog_id"]),
                algorithm_version=algorithm_version,
                preference_match_score=_required_float(item, "preference_match_score"),
                rule_fit_score=_required_float(item, "rule_fit_score"),
                value_for_money_score=_required_float(item, "value_for_money_score"),
                nlp_review_score=_optional_float(item, "nlp_review_score"),
                final_score=_required_float(item, "final_score"),
                rank_position=_required_int(item, "rank_position"),
                rationale=_required_mapping(item, "rationale"),
                generated_at=None,
            )
            for item in results
        ]
        return self.cached

    def clear_score_cache(self, *, user_id: str) -> None:
        self.cleared_cache_user_ids.append(user_id)
        self.cached = []

    def get_cached_results(
        self,
        *,
        user_id: str,
        algorithm_version: str | None = None,
    ) -> list[CachedRecommendationRecord]:
        self.last_cache_algorithm_version = algorithm_version
        return self.cached

    def get_cached_result_detail(
        self,
        *,
        user_id: str,
        catalog_id: str,
        algorithm_version: str | None = None,
    ) -> CachedRecommendationRecord | None:
        self.last_cache_algorithm_version = algorithm_version
        return next(
            (item for item in self.cached if item.catalog_id == catalog_id), None
        )


class FakeRecommendationLogRepository:
    def __init__(self) -> None:
        self.last_log: dict[str, object] | None = None
        self.last_run: dict[str, object] | None = None

    def create_log(
        self,
        *,
        user_id: str | None,
        request_payload: dict[str, object],
        response_payload: dict[str, object],
        algorithm_version: str,
    ) -> None:
        self.last_log = {
            "user_id": user_id,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "algorithm_version": algorithm_version,
        }

    def create_run(
        self,
        *,
        run_id: str,
        user_id: str | None,
        request_payload: dict[str, object],
        profile_payload: dict[str, object],
        result_payloads: list[dict[str, object]],
        algorithm_version: str,
    ) -> None:
        self.last_run = {
            "run_id": run_id,
            "user_id": user_id,
            "request_payload": request_payload,
            "profile_payload": profile_payload,
            "result_payloads": result_payloads,
            "algorithm_version": algorithm_version,
        }

    def list_logs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page:
        raise NotImplementedError

    def list_runs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page:
        raise NotImplementedError

    def get_run(self, run_id: str):
        raise NotImplementedError


def test_fyp1_scorer_uses_required_formula_and_explainability() -> None:
    candidate = FakeRecommendationRepository().list_active_candidates()[0]
    request = _attacking_request()

    result = (
        Fyp1ContentRecommendationScorer()
        .score_candidates(
            candidates=[candidate],
            request=request,
            top_n=1,
        )[0]
        .result
    )

    breakdown = result.score_breakdown or {}
    expected = (
        (breakdown["preference_match"] * 0.75) + (breakdown["rule_fit"] * 0.15)
    ) / 0.90
    assert result.score == pytest.approx(expected, abs=1e-4)
    assert result.catalog_id == "yonex-bg80"
    assert "score_breakdown" in (result.rationale_payload or {})
    assert breakdown["nlp_review_score"] is not None
    assert (result.rationale_payload or {})["nlp_review_signal_count"] >= 2
    assert (
        "review-derived signals reinforce"
        in str((result.rationale_payload or {}).get("nlp_review_summary", "")).lower()
    )
    feature_evidence = (result.rationale_payload or {}).get("feature_evidence") or []
    assert feature_evidence
    assert any(row.get("source") == "nlp_review" for row in feature_evidence)
    assert any("power and rebound" in reason.lower() for reason in result.reasons)


def test_fixed_fusion_ignores_review_popularity_and_removed_metadata() -> None:
    base = FakeRecommendationRepository().list_active_candidates()[0]

    def score_for_review_count(review_count: int) -> RecommendationResultModel:
        candidate = replace(base, item=replace(base.item, review_count=review_count))
        result = (
            Fyp1ContentRecommendationScorer()
            .score_candidates(
                candidates=[candidate],
                request=_attacking_request(),
                top_n=1,
            )[0]
            .result
        )
        return result

    unpopular = score_for_review_count(0)
    popular = score_for_review_count(100_000)

    assert unpopular.score == popular.score
    assert unpopular.aspect_scores == popular.aspect_scores
    assert "confidence_score" not in (unpopular.score_breakdown or {})
    evidence = (unpopular.rationale_payload or {})["feature_evidence"]
    assert isinstance(evidence, list)
    assert all(
        not {
            "nlp_confidence",
            "fusion_confidence",
            "source_ref",
            "source_version",
            "source_generated_at",
            "review_count_snapshot",
        }.intersection(row)
        for row in evidence
    )


def test_zero_community_feedback_preserves_baseline_scores_and_order() -> None:
    scorer = Fyp1ContentRecommendationScorer()
    candidates = FakeRecommendationRepository().list_active_candidates()
    request = _attacking_request()

    baseline = scorer.score_candidates(
        candidates=candidates,
        request=request,
        top_n=2,
    )
    empty_snapshot = scorer.score_candidates(
        candidates=candidates,
        request=request,
        top_n=2,
        community_snapshot=CommunitySnapshot(
            by_catalog={},
            snapshot_version="sha256:empty",
        ),
    )

    assert [row.result.catalog_id for row in empty_snapshot] == [
        row.result.catalog_id for row in baseline
    ]
    assert [row.result.score for row in empty_snapshot] == [
        row.result.score for row in baseline
    ]


def test_community_and_enabled_cf_are_bounded() -> None:
    scorer = Fyp1ContentRecommendationScorer()
    candidate = FakeRecommendationRepository().list_active_candidates()[0]
    request = _attacking_request()
    baseline = scorer.score_candidates(
        candidates=[candidate],
        request=request,
        top_n=1,
    )[0].result
    aggregate = CommunityFeatureAggregate(
        normalized_score=0.0,
        distinct_users=100,
        booking_count=100,
        confidence=1.0,
        weight=0.30,
        evidence_scope="global_string",
        racket_model_key=None,
        source_version="sha256:community",
    )
    snapshot = CommunitySnapshot(
        by_catalog={candidate.item.id: {"repulsion": aggregate}},
        snapshot_version="sha256:snapshot",
    )
    calibrated = scorer.score_candidates(
        candidates=[candidate],
        request=request,
        top_n=1,
        community_snapshot=snapshot,
        cf_evidence=CollaborativeEvidence(
            score_by_catalog={candidate.item.id: 1.0},
            supporting_users_by_catalog={candidate.item.id: 20},
            source_version="sha256:cf",
            eligible_interaction_count=20,
            eligible_peer_count=20,
            fallback_reason=None,
        ),
    )[0].result

    evidence = {
        row["feature_key"]: row
        for row in (calibrated.rationale_payload or {})["feature_evidence"]
    }
    assert evidence["repulsion"]["community_weight"] == pytest.approx(0.30)
    assert calibrated.score != baseline.score
    cf_evidence = (calibrated.rationale_payload or {})["cf_shadow"]
    assert cf_evidence["mode"] == "enabled"
    assert 0 < cf_evidence["cf_weight"] < 0.20
    assert (calibrated.rationale_payload or {})["collaborative_filtering_used"] is True


def test_insufficient_cf_support_preserves_exact_base_score() -> None:
    scorer = Fyp1ContentRecommendationScorer()
    candidate = FakeRecommendationRepository().list_active_candidates()[0]
    request = _attacking_request()
    baseline = scorer.score_candidates(
        candidates=[candidate], request=request, top_n=1
    )[0].result
    sparse = scorer.score_candidates(
        candidates=[candidate],
        request=request,
        top_n=1,
        cf_evidence=CollaborativeEvidence(
            score_by_catalog={candidate.item.id: 0.0},
            supporting_users_by_catalog={candidate.item.id: 2},
            source_version="sha256:sparse",
            eligible_interaction_count=2,
            eligible_peer_count=2,
            fallback_reason=None,
        ),
    )[0].result

    assert sparse.score == baseline.score
    assert (sparse.rationale_payload or {})["cf_shadow"]["cf_weight"] == 0.0
    assert (sparse.rationale_payload or {})["collaborative_filtering_used"] is False


def test_enabled_cf_can_change_ranking() -> None:
    scorer = Fyp1ContentRecommendationScorer()
    candidates = FakeRecommendationRepository().list_active_candidates()
    request = _attacking_request()
    baseline = scorer.score_candidates(candidates=candidates, request=request, top_n=2)
    first_id = baseline[0].result.catalog_id
    second_id = baseline[1].result.catalog_id
    assert first_id is not None
    assert second_id is not None

    enabled = scorer.score_candidates(
        candidates=candidates,
        request=request,
        top_n=2,
        cf_evidence=CollaborativeEvidence(
            score_by_catalog={first_id: 0.05, second_id: 1.0},
            supporting_users_by_catalog={first_id: 100, second_id: 100},
            source_version="sha256:ranking",
            eligible_interaction_count=200,
            eligible_peer_count=100,
            fallback_reason=None,
        ),
    )

    assert enabled[0].result.catalog_id == second_id
    assert enabled[0].result.score > enabled[1].result.score


def test_generate_recommendation_persists_preference_vector_and_cache() -> None:
    repository = FakeRecommendationRepository()
    logs = FakeRecommendationLogRepository()
    use_case = GenerateRecommendationUseCase(
        profile_repository=FakeProfileRepository(),
        recommendation_repository=repository,
        recommendation_log_repository=logs,
    )

    result = use_case.execute_preview(user_id="user-1", request=_attacking_request())

    assert result.algorithm_version == ALGORITHM_VERSION
    assert result.run_id
    assert result.results[0].catalog_id == "yonex-bg80"
    assert result.results[0].score_breakdown is not None
    assert logs.last_log is not None
    assert logs.last_log["algorithm_version"] == ALGORITHM_VERSION
    assert repository.preference_entries == []
    assert repository.cached == []

    profile_result = use_case._execute(
        user_id="user-1",
        request=_attacking_request(),
        persist=True,
    )
    assert profile_result.results[0].catalog_id == "yonex-bg80"
    assert {entry["feature_key"] for entry in repository.preference_entries} >= {
        "repulsion",
        "control",
        "durability",
        "comfort",
        "sound",
        "elasticity",
        "tension_retention",
        "string_movement",
        "value_for_money",
    }
    assert {entry["raw_score"] for entry in repository.preference_entries} >= {
        3.0,
        4.0,
        5.0,
    }
    assert sum(
        float(entry["preference_weight"] or 0)
        for entry in repository.preference_entries
    ) == pytest.approx(1.0, abs=1e-3)
    assert repository.cached[0].catalog_id == "yonex-bg80"
    assert repository.cached[0].preference_match_score is not None
    assert repository.cached[0].rationale["run_id"] == profile_result.run_id


def test_execute_profile_persists_true_profile_snapshot() -> None:
    repository = FakeRecommendationRepository()
    logs = FakeRecommendationLogRepository()
    profile = PlayerProfile(
        user_id="user-1",
        skill_level="advanced",
        playing_style="attacking",
        preferred_tension=27,
        frequency_per_week=4,
        preferred_feel="hard",
        preferred_gauge="thick",
        recent_goal="power",
        pref_attack=9,
        pref_comfort=3,
        pref_control=6,
        pref_durability=5,
        pref_elasticity=8,
        pref_sound=7,
        pref_string_movement=6,
        pref_tension_retention=7,
        pref_value_for_money=4,
        created_at=None,
        updated_at=None,
    )
    use_case = GenerateRecommendationUseCase(
        profile_repository=FakeProfileRepository(profile),
        recommendation_repository=repository,
        recommendation_log_repository=logs,
    )

    result = use_case.execute_profile(user_id="user-1", top_n=3)

    assert result.results
    assert logs.last_run is not None
    assert result.run_id == logs.last_run["run_id"]
    profile_payload = _required_mapping(logs.last_run, "profile_payload")
    request_payload = _required_mapping(logs.last_run, "request_payload")
    assert profile_payload["preferred_feel"] == "hard"
    assert profile_payload["preferred_gauge"] == "thick"
    assert profile_payload["recent_goal"] == "power"
    assert request_payload["top_n"] == 3
    assert "top_n" not in profile_payload


def test_profile_recommendation_rejects_unowned_racket() -> None:
    profile = PlayerProfile(
        user_id="user-1",
        skill_level="advanced",
        playing_style="balanced",
        preferred_tension=26,
        frequency_per_week=4,
        preferred_feel="medium",
        preferred_gauge="thick",
        recent_goal="balanced",
        pref_attack=5,
        pref_comfort=5,
        pref_control=5,
        pref_durability=5,
        pref_elasticity=5,
        pref_sound=5,
        pref_string_movement=5,
        pref_tension_retention=5,
        pref_value_for_money=5,
        created_at=None,
        updated_at=None,
    )
    use_case = GenerateRecommendationUseCase(
        profile_repository=FakeProfileRepository(profile),
        recommendation_repository=FakeRecommendationRepository(),
        recommendation_log_repository=FakeRecommendationLogRepository(),
    )

    with pytest.raises(NotFoundError, match="Racket not found"):
        use_case.execute_profile(
            user_id="user-1",
            top_n=3,
            racket_id="another-user-racket",
        )


def test_profile_update_invalidates_cached_recommendations() -> None:
    repository = FakeRecommendationRepository()
    profile = PlayerProfile(
        user_id="user-1",
        skill_level="beginner",
        playing_style="balanced",
        preferred_tension=22,
        frequency_per_week=1,
        preferred_feel="soft",
        preferred_gauge="thin",
        recent_goal="comfort",
        pref_attack=4,
        pref_comfort=9,
        pref_control=6,
        pref_durability=5,
        pref_elasticity=4,
        pref_sound=5,
        pref_string_movement=5,
        pref_tension_retention=5,
        pref_value_for_money=6,
        created_at=None,
        updated_at=None,
    )

    saved = UpsertMyProfileUseCase(
        profile_repository=FakeProfileRepository(),
        recommendation_repository=repository,
    ).execute(profile)

    assert saved == profile
    assert repository.cleared_cache_user_ids == ["user-1"]
    assert repository.preference_entries


def test_cached_recommendation_detail_returns_rationale() -> None:
    repository = FakeRecommendationRepository()
    logs = FakeRecommendationLogRepository()
    use_case = GenerateRecommendationUseCase(
        profile_repository=FakeProfileRepository(),
        recommendation_repository=repository,
        recommendation_log_repository=logs,
    )
    use_case._execute(user_id="user-1", request=_attacking_request(), persist=True)

    detail = use_case.execute_detail(user_id="user-1", catalog_id="yonex-bg80")

    assert detail.algorithm_version == ALGORITHM_VERSION
    assert detail.run_id
    assert detail.result.catalog_id == "yonex-bg80"
    assert detail.result.rationale_payload is not None
    assert detail.result.score_breakdown is not None
    assert detail.result.score_breakdown["nlp_review_score"] is not None
    assert detail.result.score_breakdown["final_score"] == detail.result.score
    assert repository.last_cache_algorithm_version == ALGORITHM_VERSION


def test_preference_vector_uses_defined_storage_feature_keys() -> None:
    defined_keys = {item["feature_key"] for item in RECOMMENDATION_FEATURE_DEFINITIONS}
    vector_rows = Fyp1ContentRecommendationScorer().build_preference_vector(
        user_id="user-1",
        request=_attacking_request(),
    )

    assert {row["feature_key"] for row in vector_rows}.issubset(defined_keys)
    assert {row["feature_key"] for row in vector_rows} >= {
        "repulsion",
        "sound",
        "elasticity",
        "tension_retention",
        "string_movement",
    }
    assert all(row["raw_score"] is not None for row in vector_rows)


def test_preference_weight_exponent_sharpens_priorities_without_changing_raw_scores() -> (
    None
):
    request = _attacking_request(pref_attack=10, pref_comfort=5)
    rows = Fyp1ContentRecommendationScorer(
        preference_weight_exponent=2.0
    ).build_preference_vector(user_id="offline-user", request=request)
    by_feature = {str(row["feature_key"]): row for row in rows}

    assert by_feature["repulsion"]["raw_score"] == 10
    assert by_feature["comfort"]["raw_score"] == 5
    assert float(by_feature["repulsion"]["preference_weight"] or 0) / float(
        by_feature["comfort"]["preference_weight"] or 1
    ) == pytest.approx(4.0, abs=0.01)


def test_preference_weight_exponent_must_be_positive_and_finite() -> None:
    with pytest.raises(ValueError, match="positive and finite"):
        Fyp1ContentRecommendationScorer(preference_weight_exponent=0)


def test_elasticity_preference_can_change_ranking() -> None:
    result = _score_custom_candidates(
        _attacking_request(
            pref_attack=1,
            pref_elasticity=10,
            pref_control=1,
            pref_durability=1,
            pref_comfort=1,
            pref_sound=1,
            pref_string_movement=1,
            pref_tension_retention=1,
        ),
        [
            _candidate_with_core_scores("elastic-string", {"elasticity": 0.95}),
            _candidate_with_core_scores("control-string", {"elasticity": 0.20}),
        ],
    )

    assert result.results[0].catalog_id == "elastic-string"


def test_tension_retention_preference_can_change_ranking() -> None:
    result = _score_custom_candidates(
        _attacking_request(
            pref_attack=1,
            pref_elasticity=1,
            pref_control=1,
            pref_durability=1,
            pref_comfort=1,
            pref_sound=1,
            pref_string_movement=1,
            pref_tension_retention=10,
        ),
        [
            _candidate_with_core_scores(
                "retention-string", {"tension_retention": 0.95}
            ),
            _candidate_with_core_scores("loose-string", {"tension_retention": 0.20}),
        ],
    )

    assert result.results[0].catalog_id == "retention-string"


def test_string_movement_preference_can_change_ranking() -> None:
    result = _score_custom_candidates(
        _attacking_request(
            pref_attack=1,
            pref_elasticity=1,
            pref_control=1,
            pref_durability=1,
            pref_comfort=1,
            pref_sound=1,
            pref_string_movement=10,
            pref_tension_retention=1,
        ),
        [
            _candidate_with_core_scores("stable-bed-string", {"string_movement": 0.95}),
            _candidate_with_core_scores("shifty-bed-string", {"string_movement": 0.20}),
        ],
    )

    assert result.results[0].catalog_id == "stable-bed-string"


def test_value_for_money_preference_changes_ranking() -> None:
    result = _score_custom_candidates(
        _attacking_request(
            pref_attack=1,
            pref_comfort=1,
            pref_control=1,
            pref_durability=1,
            pref_elasticity=1,
            pref_sound=1,
            pref_string_movement=1,
            pref_tension_retention=1,
            pref_value_for_money=10,
            recent_goal="value_for_money",
        ),
        [
            _candidate_with_core_scores(
                "high-value", {"value_for_money": 0.95}, price_rm=95
            ),
            _candidate_with_core_scores(
                "low-value", {"value_for_money": 0.20}, price_rm=25
            ),
        ],
    )
    assert result.results[0].catalog_id == "high-value"
    assert "budget_fit" not in (result.results[0].score_breakdown or {})


@pytest.mark.parametrize(
    ("skill_level", "preferred_tension", "frequency_per_week", "expected_catalog_id"),
    [
        ("beginner", 20, 1, "thin"),
        ("beginner", 26, 1, "thin"),
        ("advanced", 28, 1, "thick"),
        ("advanced", 25, 4, "thick"),
    ],
)
def test_profile_context_selects_expected_gauge(
    skill_level: str,
    preferred_tension: float,
    frequency_per_week: int,
    expected_catalog_id: str,
) -> None:
    request = _attacking_request(
        skill_level=skill_level,
        preferred_tension=preferred_tension,
        frequency_per_week=frequency_per_week,
    )
    result = _score_custom_candidates(
        request,
        [
            _candidate_with_core_scores("thin", {}, gauge_main_mm=0.63),
            _candidate_with_core_scores("thick", {}, gauge_main_mm=0.70),
        ],
    )
    assert result.results[0].catalog_id == expected_catalog_id


def test_explicit_gauge_and_feel_preferences_are_used() -> None:
    result = _score_custom_candidates(
        _attacking_request(
            preferred_gauge="thin",
            preferred_feel="soft",
            frequency_per_week=1,
        ),
        [
            _candidate_with_core_scores("soft-thin", {}, gauge_main_mm=0.63, feel=3.0),
            _candidate_with_core_scores("hard-thick", {}, gauge_main_mm=0.70, feel=8.0),
        ],
    )
    assert result.results[0].catalog_id == "soft-thin"
    rule_keys = {
        event["rule"]
        for event in (result.results[0].rationale_payload or {}).get("rule_events", [])
    }
    assert {"preferred_gauge_bonus", "preferred_feel_bonus"} <= rule_keys
    combined_preference_delta = result.results[0].score - result.results[1].score
    assert 0.05 <= combined_preference_delta <= 0.06


@pytest.mark.parametrize(
    ("goal", "feature_key"),
    [
        ("power", "repulsion"),
        ("control", "control"),
        ("durability", "durability"),
        ("comfort", "comfort"),
        ("tension_retention", "tension_retention"),
        ("value_for_money", "value_for_money"),
    ],
)
def test_recent_goal_is_recorded_as_a_scoring_event(
    goal: str,
    feature_key: str,
) -> None:
    result = _score_custom_candidates(
        _attacking_request(recent_goal=goal),
        [_candidate_with_core_scores("goal-fit", {feature_key: 0.95})],
    )
    events = (result.results[0].rationale_payload or {}).get("rule_events", [])
    assert any(event["rule"] == f"recent_goal_{goal}_bonus" for event in events)


def test_recent_goal_has_bounded_medium_final_score_effect() -> None:
    candidates = [
        _candidate_with_core_scores("goal-fit", {"repulsion": 0.95}),
        _candidate_with_core_scores("goal-miss", {"repulsion": 0.20}),
    ]
    baseline = _score_custom_candidates(
        _attacking_request(recent_goal="balanced"), candidates
    )
    power_goal = _score_custom_candidates(
        _attacking_request(recent_goal="power"), candidates
    )
    baseline_scores = {row.catalog_id: row.score for row in baseline.results}
    power_scores = {row.catalog_id: row.score for row in power_goal.results}

    fit_delta = power_scores["goal-fit"] - baseline_scores["goal-fit"]
    miss_delta = power_scores["goal-miss"] - baseline_scores["goal-miss"]
    assert 0.016 <= fit_delta <= 0.017
    assert -0.009 <= miss_delta <= -0.008
    assert 0.024 <= fit_delta - miss_delta <= 0.026


def test_profile_payload_rejects_legacy_budget_range_fields() -> None:
    with pytest.raises(ValidationError):
        ProfilePayload.model_validate(
            {
                "skill_level": "advanced",
                "playing_style": "attacking",
                "budget_tier": "below_30",
                "budget_min": 50,
                "budget_max": 80,
            }
        )


def test_recommendation_request_rejects_legacy_budget_range_fields() -> None:
    with pytest.raises(ValidationError):
        RecommendationRequestDto.model_validate(
            {
                "user_id": "user-1",
                "skill_level": "advanced",
                "playing_style": "attacking",
                "budget_tier": "above_50",
                "preferred_tension": 26,
                "game_type": "doubles",
                "frequency_per_week": 3,
                "preferred_feel": "hard",
                "preferred_gauge": "thick",
                "recent_goal": "power",
                "pref_attack": 5,
                "pref_comfort": 3,
                "pref_control": 4,
                "pref_durability": 3,
                "pref_elasticity": 5,
                "pref_sound": 4,
                "pref_string_movement": 3,
                "pref_tension_retention": 4,
                "pref_value_for_money": 3,
                "top_n": 3,
                "budget_min": 0,
                "budget_max": 30,
            }
        )


def _attacking_request(
    *,
    pref_attack: int = 5,
    pref_comfort: int = 3,
    pref_control: int = 4,
    pref_durability: int = 3,
    pref_elasticity: int = 5,
    pref_sound: int = 4,
    pref_string_movement: int = 3,
    pref_tension_retention: int = 4,
    pref_value_for_money: int = 3,
    skill_level: str = "advanced",
    preferred_tension: float = 26,
    frequency_per_week: int = 3,
    preferred_feel: str = "medium",
    preferred_gauge: str = "no_preference",
    recent_goal: str = "balanced",
) -> RecommendationRequestModel:
    return RecommendationRequestModel(
        user_id="user-1",
        skill_level=skill_level,
        playing_style="attacking",
        preferred_tension=preferred_tension,
        frequency_per_week=frequency_per_week,
        preferred_feel=preferred_feel,
        preferred_gauge=preferred_gauge,
        recent_goal=recent_goal,
        pref_attack=pref_attack,
        pref_comfort=pref_comfort,
        pref_control=pref_control,
        pref_durability=pref_durability,
        pref_elasticity=pref_elasticity,
        pref_sound=pref_sound,
        pref_string_movement=pref_string_movement,
        pref_tension_retention=pref_tension_retention,
        pref_value_for_money=pref_value_for_money,
        top_n=3,
    )


def _string_item(
    *,
    id: str,
    display_name: str,
    model_name: str,
    price_rm: float,
    gauge_main_mm: float,
) -> StringItem:
    base = StringItem(
        id=id,
        brand="Yonex",
        brand_code="yonex",
        display_name=display_name,
        model_name=model_name,
        normalized_name=display_name.lower(),
        series_key="high_repulsion",
        series_label="High Repulsion",
        is_hybrid=False,
        gauge_main_mm=gauge_main_mm,
        gauge_cross_mm=None,
        gauge_label=f"{gauge_main_mm:.2f} mm",
        category="repulsion",
        main_trait="Crisp response",
        tension_min_lbs=22,
        tension_max_lbs=29,
        material_summary_en="Nylon multifilament",
        image_url=None,
        color_options_en=["White"],
        short_description="Short description",
        full_description="Full description",
        official_performance_status="pending_manual_fill",
        source_dataset_url=None,
        source_language="en",
        original_name=model_name,
        original_brand_label="尤尼克斯 YONEX",
        original_series="高弹性",
        original_material=None,
        original_color=None,
        community_rating=9.1,
        want_count=100,
        used_count=50,
        review_count=20,
        tags=[],
        official_performance=None,
        inventory=InventorySnapshot(
            inventory_id=f"{id}-inventory",
            current_stock=8,
            reserved_stock=0,
            available_stock=8,
            reorder_level=3,
            reorder_quantity=8,
            cost_price=None,
            selling_price=price_rm,
            pricing_mode="fixed_price",
            availability_status="in_stock",
            is_active=True,
            latest_note=None,
            updated_at=None,
        ),
        aspect_scores={},
        is_active=True,
        created_at=None,
        updated_at=None,
    )
    return base


def _candidate(
    *,
    id: str,
    display_name: str,
    model_name: str,
    price_rm: float,
    gauge_main_mm: float,
    nlp_scores: dict[str, float],
) -> RecommendationCandidateModel:
    return RecommendationCandidateModel(
        item=_string_item(
            id=id,
            display_name=display_name,
            model_name=model_name,
            price_rm=price_rm,
            gauge_main_mm=gauge_main_mm,
        ),
        matrix_by_source={"nlp_review": nlp_scores},
    )


def _candidate_with_core_scores(
    catalog_id: str,
    overrides: dict[str, float],
    *,
    price_rm: float = 45,
    gauge_main_mm: float = 0.68,
    feel: float | None = None,
) -> RecommendationCandidateModel:
    base_scores = {
        "attack": 0.50,
        "comfort": 0.50,
        "control": 0.50,
        "durability": 0.50,
        "elasticity": 0.50,
        "sound": 0.50,
        "string_movement": 0.50,
        "tension_retention": 0.50,
        "value_for_money": 0.50,
    }
    base_scores.update(overrides)
    candidate = _candidate(
        id=catalog_id,
        display_name=catalog_id.replace("-", " ").title(),
        model_name=catalog_id,
        price_rm=price_rm,
        gauge_main_mm=gauge_main_mm,
        nlp_scores=base_scores,
    )
    if feel is None:
        return candidate
    official = StringOfficialPerformance(
        catalog_id=catalog_id,
        source_type="curated",
        source_name="test",
        source_url=None,
        source_region=None,
        category=None,
        feature=None,
        feel=feel,
        repulsion_power=None,
        durability=None,
        hitting_sound=None,
        shock_absorption=None,
        control=None,
        notes=None,
        status="manual_reviewed",
        updated_at=None,
    )
    return replace(
        candidate, item=replace(candidate.item, official_performance=official)
    )


def _score_custom_candidates(
    request: RecommendationRequestModel,
    candidates: list[RecommendationCandidateModel],
):
    return GenerateRecommendationUseCase(
        profile_repository=FakeProfileRepository(),
        recommendation_repository=FakeRecommendationRepository(candidates),
        recommendation_log_repository=FakeRecommendationLogRepository(),
    ).execute_preview(user_id="user-1", request=request)


def _required_float(values: dict[str, object], key: str) -> float:
    value = values[key]
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value for {key}")


def _optional_float(values: dict[str, object], key: str) -> float | None:
    value = values.get(key)
    if value is None:
        return None
    if isinstance(value, int | float | str):
        return float(value)
    raise TypeError(f"Expected numeric value for {key}")


def _required_int(values: dict[str, object], key: str) -> int:
    value = values[key]
    if isinstance(value, int | str):
        return int(value)
    raise TypeError(f"Expected integer value for {key}")


def _required_mapping(values: dict[str, object], key: str) -> dict[str, object]:
    value = values[key]
    if isinstance(value, Mapping):
        return dict(value)
    raise TypeError(f"Expected mapping value for {key}")
