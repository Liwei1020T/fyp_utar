from __future__ import annotations

from collections.abc import Mapping

import pytest

from app.domain.profile.entities import PlayerProfile
from app.domain.catalog.entities import InventorySnapshot
from app.domain.catalog.entities import StringItem
from app.domain.catalog.recommendation_features import (
    RECOMMENDATION_FEATURE_DEFINITIONS,
)
from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.domain.recommendation.scoring import Fyp1ContentRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.dto.profile import ProfilePayload
from app.dto.recommendation import RecommendationRequestDto
from app.shared.pagination import Page
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)


class FakeProfileRepository:
    def __init__(self, profile: PlayerProfile | None = None) -> None:
        self.profile = profile

    def get_by_user_id(self, user_id: str):  # pragma: no cover - not used here
        if self.profile is not None:
            return self.profile
        raise AssertionError("profile lookup should not be used for preview requests")

    def upsert(self, profile):  # pragma: no cover - not used here
        raise NotImplementedError


class FakeRecommendationRepository:
    def __init__(
        self,
        candidates: list[RecommendationCandidateModel] | None = None,
    ) -> None:
        self.preference_entries: list[dict[str, float | str | None]] = []
        self.cached: list[CachedRecommendationRecord] = []
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
                budget_fit_score=_required_float(item, "budget_fit_score"),
                confidence_score=_required_float(item, "confidence_score"),
                nlp_review_score=_optional_float(item, "nlp_review_score"),
                final_score=_required_float(item, "final_score"),
                rank_position=_required_int(item, "rank_position"),
                rationale=_required_mapping(item, "rationale"),
                matrix_version=_optional_str(item, "matrix_version"),
                feature_source_version=_optional_str(item, "feature_source_version"),
                generated_at=None,
            )
            for item in results
        ]
        return self.cached

    def get_cached_results(
        self,
        *,
        user_id: str,
        algorithm_version: str | None = None,
    ) -> list[CachedRecommendationRecord]:
        return self.cached

    def get_cached_result_detail(
        self,
        *,
        user_id: str,
        catalog_id: str,
        algorithm_version: str | None = None,
    ) -> CachedRecommendationRecord | None:
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
        user_id: str | None,
        request_payload: dict[str, object],
        profile_payload: dict[str, object],
        result_payloads: list[dict[str, object]],
        algorithm_version: str,
        matrix_version: str | None,
        feature_source_version: str | None,
    ) -> None:
        self.last_run = {
            "user_id": user_id,
            "request_payload": request_payload,
            "profile_payload": profile_payload,
            "result_payloads": result_payloads,
            "algorithm_version": algorithm_version,
            "matrix_version": matrix_version,
            "feature_source_version": feature_source_version,
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
        (breakdown["preference_match"] * 0.60)
        + (breakdown["rule_fit"] * 0.15)
        + (breakdown["budget_fit"] * 0.15)
        + (breakdown["confidence_score"] * 0.10)
    )
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
    assert result.results[0].catalog_id == "yonex-bg80"
    assert result.results[0].score_breakdown is not None
    assert logs.last_log is not None
    assert logs.last_log["algorithm_version"] == ALGORITHM_VERSION

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


def test_execute_profile_persists_true_profile_snapshot() -> None:
    repository = FakeRecommendationRepository()
    logs = FakeRecommendationLogRepository()
    profile = PlayerProfile(
        user_id="user-1",
        skill_level="advanced",
        playing_style="attacking",
        budget_tier="between_30_50",
        budget_min=40,
        budget_max=70,
        preferred_tension=27,
        game_type="doubles",
        frequency_per_week=4,
        preferred_feel="crisp",
        recent_goal="Need a sharp doubles setup.",
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
    profile_payload = _required_mapping(logs.last_run, "profile_payload")
    request_payload = _required_mapping(logs.last_run, "request_payload")
    assert profile_payload["preferred_feel"] == "crisp"
    assert profile_payload["recent_goal"] == ("Need a sharp doubles setup.")
    assert request_payload["top_n"] == 3
    assert "top_n" not in profile_payload


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
    assert detail.result.catalog_id == "yonex-bg80"
    assert detail.result.rationale_payload is not None
    assert detail.result.score_breakdown is not None
    assert detail.result.score_breakdown["nlp_review_score"] is not None
    assert detail.result.score_breakdown["final_score"] == detail.result.score


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


def test_budget_fit_softens_below_minimum_and_penalizes_above_maximum() -> None:
    result = _score_custom_candidates(
        _attacking_request(),
        [
            _candidate_with_core_scores("inside-budget", {}, price_rm=45),
            _candidate_with_core_scores("below-minimum", {}, price_rm=25),
            _candidate_with_core_scores("above-maximum", {}, price_rm=95),
        ],
    )
    breakdowns = {
        item.catalog_id: item.score_breakdown or {} for item in result.results
    }

    assert breakdowns["inside-budget"]["budget_fit"] >= 0.8
    assert breakdowns["below-minimum"]["budget_fit"] >= 0.62
    assert (
        breakdowns["above-maximum"]["budget_fit"]
        < breakdowns["below-minimum"]["budget_fit"]
    )


def test_profile_payload_rejects_conflicting_budget_tier_and_range() -> None:
    with pytest.raises(ValueError, match="budget_tier must match"):
        ProfilePayload(
            skill_level="advanced",
            playing_style="attacking",
            budget_tier="below_30",
            budget_min=50,
            budget_max=80,
        )


def test_recommendation_request_rejects_conflicting_budget_tier_and_range() -> None:
    with pytest.raises(ValueError, match="budget_tier must match"):
        RecommendationRequestDto(
            user_id="user-1",
            skill_level="advanced",
            playing_style="attacking",
            budget_tier="above_50",
            budget_min=0,
            budget_max=30,
            preferred_tension=26,
            game_type="doubles",
            frequency_per_week=3,
            pref_attack=5,
            pref_comfort=3,
            pref_control=4,
            pref_durability=3,
            pref_elasticity=5,
            pref_sound=4,
            pref_string_movement=3,
            pref_tension_retention=4,
            pref_value_for_money=3,
            top_n=3,
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
) -> RecommendationRequestModel:
    return RecommendationRequestModel(
        user_id="user-1",
        skill_level="advanced",
        playing_style="attacking",
        budget_tier="between_30_50",
        budget_min=40,
        budget_max=70,
        preferred_tension=26,
        game_type="doubles",
        frequency_per_week=3,
        pref_attack=pref_attack,
        pref_comfort=pref_comfort,
        pref_control=pref_control,
        pref_durability=pref_durability,
        pref_elasticity=pref_elasticity,
        pref_sound=pref_sound,
        pref_string_movement=pref_string_movement,
        pref_tension_retention=pref_tension_retention,
        pref_value_for_money=3,
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
    return _candidate(
        id=catalog_id,
        display_name=catalog_id.replace("-", " ").title(),
        model_name=catalog_id,
        price_rm=price_rm,
        gauge_main_mm=0.68,
        nlp_scores=base_scores,
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


def _optional_str(values: dict[str, object], key: str) -> str | None:
    value = values.get(key)
    return value if isinstance(value, str) else None


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
