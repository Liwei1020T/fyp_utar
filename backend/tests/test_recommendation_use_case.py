from __future__ import annotations

from collections.abc import Mapping

import pytest

from app.domain.catalog.entities import InventorySnapshot
from app.domain.catalog.entities import StringItem
from app.domain.catalog.recommendation_features import (
    RECOMMENDATION_FEATURE_DEFINITIONS,
)
from app.domain.recommendation.entities import CachedRecommendationRecord
from app.domain.recommendation.entities import RecommendationCandidateModel
from app.domain.recommendation.entities import RecommendationRequestModel
from app.domain.recommendation.scoring import ALGORITHM_VERSION
from app.domain.recommendation.scoring import HybridRecommendationScorer
from app.domain.recommendation.scoring import PREFERENCE_SOURCE_LAYER
from app.shared.pagination import Page
from app.use_cases.recommendation.generate_recommendation import (
    GenerateRecommendationUseCase,
)


class FakeProfileRepository:
    def get_by_user_id(self, user_id: str):  # pragma: no cover - not used here
        raise AssertionError("profile lookup should not be used for preview requests")

    def upsert(self, profile):  # pragma: no cover - not used here
        raise NotImplementedError


class FakeRecommendationRepository:
    def __init__(self) -> None:
        self.preference_entries: list[dict[str, float | str | None]] = []
        self.cached: list[CachedRecommendationRecord] = []

    def list_active_candidates(self) -> list[RecommendationCandidateModel]:
        return [
            RecommendationCandidateModel(
                item=_string_item(
                    id="yonex-bg80",
                    display_name="Yonex BG80",
                    model_name="BG80",
                    price_rm=45,
                    gauge_main_mm=0.68,
                ),
                matrix_by_source={
                    "nlp_review": {
                        "attack": 0.92,
                        "comfort": 0.42,
                        "control": 0.71,
                        "durability": 0.61,
                        "elasticity": 0.88,
                        "sound": 0.86,
                        "value_for_money": 0.58,
                    }
                },
            ),
            RecommendationCandidateModel(
                item=_string_item(
                    id="yonex-bg65",
                    display_name="Yonex BG65",
                    model_name="BG65",
                    price_rm=43,
                    gauge_main_mm=0.70,
                ),
                matrix_by_source={
                    "nlp_review": {
                        "attack": 0.51,
                        "comfort": 0.76,
                        "control": 0.67,
                        "durability": 0.89,
                        "elasticity": 0.45,
                        "sound": 0.41,
                        "value_for_money": 0.82,
                    }
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
                nlp_review_score=_required_float(item, "nlp_review_score"),
                final_score=_required_float(item, "final_score"),
                rank_position=_required_int(item, "rank_position"),
                rationale=_required_mapping(item, "rationale"),
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

    def list_logs(
        self,
        *,
        phone_number: str | None,
        algorithm_version: str | None,
        limit: int | None,
        offset: int,
    ) -> Page:
        raise NotImplementedError


def test_hybrid_scorer_uses_required_formula_and_explainability() -> None:
    candidate = FakeRecommendationRepository().list_active_candidates()[0]
    request = _attacking_request()

    result = (
        HybridRecommendationScorer()
        .score_candidates(
            candidates=[candidate],
            request=request,
            top_n=1,
        )[0]
        .result
    )

    breakdown = result.score_breakdown or {}
    expected = (
        (breakdown["preference_match"] * 0.55)
        + (breakdown["rule_fit"] * 0.20)
        + (breakdown["budget_fit"] * 0.15)
        + (breakdown["nlp_review_score"] * 0.10)
    )
    assert result.score == pytest.approx(expected, abs=1e-4)
    assert result.catalog_id == "yonex-bg80"
    assert "score_breakdown" in (result.rationale_payload or {})
    assert any("attack" in reason.lower() for reason in result.reasons)


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
        "attack",
        "gauge_mm",
        "hitting_sound",
        "price_rm",
    }
    assert "sound" not in {
        entry["feature_key"] for entry in repository.preference_entries
    }
    assert repository.cached[0].catalog_id == "yonex-bg80"
    assert repository.cached[0].preference_match_score is not None


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
    assert detail.result.score_breakdown["final_score"] == detail.result.score


def test_preference_vector_uses_defined_storage_feature_keys() -> None:
    defined_keys = {item["feature_key"] for item in RECOMMENDATION_FEATURE_DEFINITIONS}
    vector_rows = HybridRecommendationScorer().build_preference_vector(
        user_id="user-1",
        request=_attacking_request(),
    )

    assert {row["feature_key"] for row in vector_rows}.issubset(defined_keys)
    assert "hitting_sound" in {row["feature_key"] for row in vector_rows}
    assert "sound" not in {row["feature_key"] for row in vector_rows}


def _attacking_request() -> RecommendationRequestModel:
    return RecommendationRequestModel(
        user_id="user-1",
        skill_level="advanced",
        playing_style="attacking",
        budget_min=40,
        budget_max=70,
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
        material_summary_en="Nylon multifilament",
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


def _required_float(values: dict[str, object], key: str) -> float:
    value = values[key]
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
