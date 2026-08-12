import os

from ai_service import data_loader
from ai_service.core.config import BACKEND_ROOT
from ai_service.schemas import RecommendationRequest
from ai_service.service import RecommendationService


def test_recommendation_service_prefers_attacking_string_from_matrix_fixture(tmp_path):
    matrix_path = tmp_path / "matrix.csv"
    matrix_path.write_text(
        "\n".join(
            [
                "brand,model_name,price_rm,attack,comfort,control,durability,elasticity,sound,string_movement,tension_retention,value_for_money,beginner_fit_score,stability_score,all_round_score",
                "Yonex,BG80,45,0.92,0.42,0.71,0.61,0.88,0.86,0.65,0.62,0.58,0.5,0.61,0.73",
                "Yonex,BG65,43,0.51,0.76,0.67,0.89,0.45,0.41,0.72,0.8,0.82,0.83,0.86,0.7",
            ]
        ),
        encoding="utf-8",
    )

    os.environ["AI_MATRIX_CSV_PATH"] = str(matrix_path)
    data_loader.load_string_matrix.cache_clear()
    service = RecommendationService()

    response = service.recommend(
        RecommendationRequest(
            skill_level="advanced",
            playing_style="attacking",
            preferred_tension=26,
            frequency_per_week=4,
            pref_attack=5,
            pref_comfort=2,
            pref_control=3,
            pref_durability=3,
            pref_elasticity=5,
            pref_sound=4,
            pref_string_movement=3,
            pref_tension_retention=3,
            pref_value_for_money=2,
            top_n=2,
        )
    )

    assert response.results[0].string_name == "Yonex BG80"
    assert any("attacking" in reason.lower() for reason in response.results[0].reasons)


def test_get_string_accepts_brand_and_punctuation_aliases(tmp_path):
    fallback_path = tmp_path / "catalog.jsonl"
    fallback_path.write_text(
        "\n".join(
            [
                '{"brand":"尤尼克斯 YONEX","name":"BG-80","price":68,"gauge":"0.68mm","top_tags":["弹性好"],"tags":[{"name":"弹性好","votes":10}]}',
            ]
        ),
        encoding="utf-8",
    )

    os.environ["AI_MATRIX_CSV_PATH"] = str(tmp_path / "missing-matrix.csv")
    os.environ["AI_FALLBACK_JSONL_PATH"] = str(fallback_path)
    data_loader.load_string_matrix.cache_clear()
    service = RecommendationService()

    for alias in ("BG-80", "Yonex BG-80", "yonex bg 80"):
        result = service.get_string(alias)
        assert result["model_name"] == "BG-80"


def test_relative_fallback_catalog_path_resolves_from_backend_root():
    os.environ["AI_FALLBACK_JSONL_PATH"] = "data/raw/custom-catalog.jsonl"

    resolved_path = data_loader.get_fallback_jsonl_path()

    assert resolved_path == BACKEND_ROOT / "data/raw/custom-catalog.jsonl"


def test_default_matrix_path_uses_canonical_latest_csv(monkeypatch):
    monkeypatch.delenv("AI_MATRIX_CSV_PATH", raising=False)

    resolved_path = data_loader.get_matrix_path()

    assert resolved_path == (
        BACKEND_ROOT
        / "../ml/nlp-workbench-latest/output/latest_practical_string_feature_matrix_v8_v6dict.csv"
    )
