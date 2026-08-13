from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd
import pytest
import numpy as np


WORKBENCH = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WORKBENCH / "src"))

from stringsense_nlp.bert import BERT_LABELS  # noqa: E402
from stringsense_nlp.bert import BASELINE_MODEL_NAME  # noqa: E402
from stringsense_nlp.bert import build_bert_pseudo_dataset  # noqa: E402
from stringsense_nlp.bert import default_training_config  # noqa: E402
from stringsense_nlp.bert import filter_bert_string_cohort  # noqa: E402
from stringsense_nlp.bert import format_bert_model_input  # noqa: E402
from stringsense_nlp.bert import load_bert_string_cohort  # noqa: E402
from stringsense_nlp.bert import validate_bert_pseudo_dataset  # noqa: E402
from stringsense_nlp.bert_inference import aggregate_candidate_cells  # noqa: E402
from stringsense_nlp.bert_inference import build_inference_frame  # noqa: E402
from stringsense_nlp.bert_inference import choose_minimum_evidence  # noqa: E402
from stringsense_nlp.bert_inference import choose_pilot_threshold  # noqa: E402
from stringsense_nlp.bert_inference import load_inference_catalog  # noqa: E402
from stringsense_nlp.bert_inference import mark_aggregation_status  # noqa: E402
from stringsense_nlp.bert_inference import minimum_evidence_analysis  # noqa: E402
from stringsense_nlp.bert_inference import threshold_analysis  # noqa: E402
from stringsense_nlp.bert_inference import validate_inference_request  # noqa: E402
from stringsense_nlp.bert_review import build_cell_stability  # noqa: E402
from stringsense_nlp.bert_review import build_evidence_status_delta  # noqa: E402
from stringsense_nlp.bert_review import build_operational_review  # noqa: E402
from stringsense_nlp.bert_review import build_profile_audit  # noqa: E402
from stringsense_nlp.bert_review import build_threshold_comparison  # noqa: E402
from stringsense_nlp.bert_review import compare_candidate_cells  # noqa: E402
from stringsense_nlp.bert_review import _sensitivity_report  # noqa: E402
from stringsense_nlp.bert_review import load_system_catalog_snapshot  # noqa: E402
from stringsense_nlp.bert_review import summarize_profile_movements  # noqa: E402
from scripts.train_bert import _confusion_matrix  # noqa: E402
from scripts.train_bert import _limit_splits  # noqa: E402
from scripts.train_bert import _metrics  # noqa: E402
from scripts.train_bert import _verify_dataset_sha256  # noqa: E402


def _mappings() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "normalized_name": "bg80",
                "canonical_name": "Yonex BG80",
                "review_status": "confirmed",
            }
        ]
    )


def _silver() -> pd.DataFrame:
    labels = ("not_mentioned", "positive", "negative", "mentioned", "mixed")
    return pd.DataFrame(
        [
            {
                "sample_id": f"R{index}_control",
                "split": split,
                "split_group_id": f"group-{index}",
                "review_id": f"R{index}",
                "string_name": "BG-80",
                "review_text": f"review {index}",
                "aspect": "control",
                "label_text": label,
                "needs_manual_review": int(label in {"mentioned", "mixed"}),
            }
            for index, (split, label) in enumerate(
                zip(("train", "val", "test", "val", "test"), labels, strict=True),
                start=1,
            )
        ]
    )


def test_bert_pseudo_labels_are_traceable_and_not_human_gold() -> None:
    dataset = build_bert_pseudo_dataset(_silver(), _mappings())
    report = validate_bert_pseudo_dataset(dataset)

    assert (
        tuple(dataset.sort_values("bert_label_id")["bert_label"].unique())
        == BERT_LABELS
    )
    assert set(dataset["source_silver_label"]) == set(BERT_LABELS)
    assert set(dataset["pseudo_label_confidence"]) == {"high"}
    assert not dataset["needs_manual_review"].any()
    assert (
        dataset["model_input"].str.contains("目标球线：Yonex BG80", regex=False).all()
    )
    assert not dataset["human_gold"].any()
    assert report["leakage"]["review_cross_partition_count"] == 0
    assert report["label_policy"] == "high_confidence_silver_three_class"
    assert report["evaluation_status"] == "pseudo_label_validation_only"


def test_bert_preparation_rejects_unresolved_string_names() -> None:
    silver = _silver()
    silver["string_name"] = "unknown"

    with pytest.raises(ValueError, match="unresolved string names"):
        build_bert_pseudo_dataset(silver, _mappings())


def test_bert_validation_rejects_low_confidence_rows() -> None:
    dataset = build_bert_pseudo_dataset(_silver(), _mappings())
    dataset.loc[0, "pseudo_label_confidence"] = "low"

    with pytest.raises(ValueError, match="high-confidence Silver rows only"):
        validate_bert_pseudo_dataset(dataset)


def test_bert_cohort_v1_selects_the_approved_twelve_strings() -> None:
    cohort = load_bert_string_cohort(
        WORKBENCH.parents[1] / "config/approved_string_cohort_v1.csv"
    )
    dataset = build_bert_pseudo_dataset(_silver(), _mappings())
    filtered = filter_bert_string_cohort(dataset, ("Yonex BG80",))

    assert len(cohort) == 12
    assert set(cohort) == {
        "Yonex BG80",
        "Yonex BG65",
        "Yonex BG66 ULTIMAX",
        "Yonex BG80 POWER",
        "Yonex EXBOLT 63",
        "Yonex AEROBITE",
        "Victor VBS-66 NANO",
        "Victor VBS-68 Power",
        "Li-Ning No.1",
        "Li-Ning N65",
        "Gosen RYZONIC 65",
        "Kumpoo JS-63",
    }
    assert set(filtered["canonical_string_name"]) == {"Yonex BG80"}


def test_training_config_marks_the_comparison_baseline() -> None:
    config = default_training_config(BASELINE_MODEL_NAME, seed=42)

    assert config["model_role"] == "baseline"
    assert config["primary_model_name"] == "hfl/chinese-macbert-base"
    assert config["labels"] == ["not_mentioned", "positive", "negative"]
    assert config["task"] == "aspect_conditioned_three_class_sequence_classification"


def test_training_benchmark_sampling_and_metrics_cover_each_class() -> None:
    frame = pd.DataFrame(
        {
            "sample_id": [f"sample-{index}" for index in range(12)],
            "split": ["train"] * 6 + ["val"] * 6,
        }
    )
    sample = _limit_splits(frame, size=3, seed=42)
    predictions = np.array([[9, 1, 0], [0, 8, 1], [0, 1, 7]])
    labels = np.array([0, 1, 2])

    assert sample.groupby("split").size().to_dict() == {"train": 3, "val": 3}
    assert (
        sample["sample_id"].tolist()
        == _limit_splits(frame, size=3, seed=42)["sample_id"].tolist()
    )
    assert _metrics(predictions, labels)["f1_negative"] == 1.0
    assert _confusion_matrix(predictions, labels)["rows_true_columns_predicted"] == [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
    ]


def test_portable_training_requires_the_exact_dataset_digest(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset.csv"
    dataset.write_text("review,label\n稳定,positive\n", encoding="utf-8")
    actual = _verify_dataset_sha256(dataset, "")

    assert _verify_dataset_sha256(dataset, actual) == actual
    with pytest.raises(ValueError, match="Dataset SHA256 mismatch"):
        _verify_dataset_sha256(dataset, "0" * 64)


def test_inference_reuses_training_input_and_rejects_unknown_scope() -> None:
    catalog = load_inference_catalog(
        WORKBENCH.parents[1] / "config/approved_string_cohort_v1.csv"
    )
    expected = "目标球线：Yonex BG80\n评价方面：控制\n评论：控球很稳"

    assert format_bert_model_input("Yonex BG80", "control", "控球很稳") == expected
    assert (
        validate_inference_request("Yonex BG80", "control", "控球很稳", catalog)
        == expected
    )
    with pytest.raises(ValueError, match="outside the approved"):
        validate_inference_request("Yonex Unknown", "control", "控球很稳", catalog)
    with pytest.raises(ValueError, match="Unsupported BERT aspect"):
        validate_inference_request("Yonex BG80", "speed", "控球很稳", catalog)


def test_inference_frame_expands_each_real_review_to_nine_aspects() -> None:
    catalog = load_inference_catalog(
        WORKBENCH.parents[1] / "config/approved_string_cohort_v1.csv"
    )
    dataset = pd.DataFrame(
        [
            {
                "review_id": f"R{index}",
                "split": "test",
                "split_group_id": f"group-{index}",
                "string_name": name,
                "canonical_string_name": name,
                "review_text": f"真实评论 {index}",
                "sample_id": f"R{index}_control",
                "bert_label": "positive",
            }
            for index, name in enumerate(catalog["canonical_string_name"], start=1)
        ]
    )

    frame = build_inference_frame(dataset, catalog, "dataset-run")

    assert len(frame) == 12 * 9
    assert frame["review_id"].nunique() == 12
    assert set(frame["aspect"]) == set(
        (
            "attack",
            "comfort",
            "control",
            "durability",
            "elasticity",
            "sound",
            "string_movement",
            "tension_retention",
            "value_for_money",
        )
    )
    assert (frame["source_silver_label"] == "positive").sum() == 12


def test_pilot_gate_balances_silver_error_and_coverage() -> None:
    evidence = pd.DataFrame(
        [
            {
                "split": "test",
                "source_silver_label": "positive",
                "predicted_label": "positive",
                "confidence": 0.85,
            }
            for _ in range(10)
        ]
        + [
            {
                "split": "test",
                "source_silver_label": "not_mentioned",
                "predicted_label": "positive",
                "confidence": 0.75,
            }
        ]
    )

    analysis = threshold_analysis(evidence, candidates=(0.70, 0.80))

    assert choose_pilot_threshold(analysis) == 0.80
    assert analysis.iloc[0]["accepted_directional_errors"] == 1
    assert analysis.iloc[1]["directional_silver_recall"] == 1.0


def test_candidate_review_keeps_validation_and_test_thresholds_separate() -> None:
    rows = []
    for split, correct_rows in (("val", 100), ("test", 98)):
        rows.extend(
            {
                "split": split,
                "source_silver_label": "positive",
                "predicted_label": "positive",
                "confidence": 0.999,
            }
            for _ in range(correct_rows)
        )
        rows.append(
            {
                "split": split,
                "source_silver_label": "not_mentioned",
                "predicted_label": "positive",
                "confidence": 0.994,
            }
        )

    comparison = build_threshold_comparison(
        pd.DataFrame(rows), candidates=(0.99, 0.995)
    )
    selected = comparison[comparison["selected_under_existing_policy"]]

    assert selected.set_index("split")["confidence_threshold"].to_dict() == {
        "val": 0.99,
        "test": 0.995,
    }


def test_operational_review_requires_exact_accepted_test_disagreements() -> None:
    evidence = pd.DataFrame(
        [
            {
                "source_sample_id": "R1_control",
                "split": "test",
                "source_silver_label": "not_mentioned",
                "predicted_label": "positive",
                "confidence": 0.999,
                "aspect": "control",
            },
            {
                "source_sample_id": "R2_control",
                "split": "test",
                "source_silver_label": "positive",
                "predicted_label": "positive",
                "confidence": 0.999,
                "aspect": "control",
            },
        ]
    )
    decisions = pd.DataFrame(
        [
            {
                "source_sample_id": "R1_control",
                "assistant_operational_verdict": "model_supported",
                "error_type": "silver_aspect_omission",
                "review_note": "explicit control wording",
            }
        ]
    )

    reviewed = build_operational_review(evidence, decisions, threshold=0.995)

    assert reviewed["source_sample_id"].tolist() == ["R1_control"]
    assert reviewed["review_status"].unique().tolist() == [
        "codex_assisted_pending_owner_approval"
    ]
    assert not reviewed["human_gold"].any()
    with pytest.raises(ValueError, match="cover exactly"):
        build_operational_review(evidence, decisions.iloc[0:0], threshold=0.995)


def test_candidate_cell_stability_reports_descriptive_wilson_interval() -> None:
    cells = pd.DataFrame(
        [
            {
                "canonical_string_name": "Kumpoo JS-63",
                "aspect": "control",
                "accepted_evidence_count": 33,
                "positive_evidence_count": 30,
                "normalized_score_0_to_1": 30 / 33,
            }
        ]
    )

    stability = build_cell_stability(cells).iloc[0]

    assert stability["positive_share_wilson_95_lower"] == pytest.approx(0.7643, 1e-4)
    assert stability["positive_share_wilson_95_upper"] == pytest.approx(0.9686, 1e-4)
    assert stability["score_1_to_5_wilson_95_lower"] > 4.0


def test_lower_threshold_records_only_changed_evidence_statuses() -> None:
    evidence = pd.DataFrame(
        [
            {
                "source_sample_id": "R1_control",
                "predicted_label": "positive",
                "confidence": 0.85,
                "aggregation_status": "low_confidence_excluded",
            },
            {
                "source_sample_id": "R2_control",
                "predicted_label": "positive",
                "confidence": 0.999,
                "aggregation_status": "accepted_directional",
            },
            {
                "source_sample_id": "R3_control",
                "predicted_label": "not_mentioned",
                "confidence": 0.85,
                "aggregation_status": "low_confidence_excluded",
            },
        ]
    )

    sensitivity, delta = build_evidence_status_delta(evidence, threshold=0.8)

    assert sensitivity["aggregation_status"].tolist() == [
        "accepted_directional",
        "accepted_directional",
        "not_mentioned_excluded",
    ]
    assert delta["source_sample_id"].tolist() == ["R1_control", "R3_control"]


def test_candidate_cell_comparison_reports_added_evidence_and_score_delta() -> None:
    confirmed = pd.DataFrame(
        [
            {
                "canonical_string_name": "Yonex BG80",
                "aspect": "control",
                "accepted_evidence_count": 10,
                "positive_evidence_count": 8,
                "negative_evidence_count": 2,
                "normalized_score_0_to_1": 0.8,
                "score_1_to_5": 4.2,
            }
        ]
    )
    sensitivity = confirmed.copy()
    sensitivity.loc[0, "accepted_evidence_count"] = 12
    sensitivity.loc[0, "positive_evidence_count"] = 9
    sensitivity.loc[0, "negative_evidence_count"] = 3
    sensitivity.loc[0, "normalized_score_0_to_1"] = 0.75
    sensitivity.loc[0, "score_1_to_5"] = 4.0

    comparison = compare_candidate_cells(sensitivity, confirmed).iloc[0]

    assert comparison["accepted_evidence_added"] == 2
    assert comparison["normalized_score_delta"] == pytest.approx(-0.05)
    assert comparison["score_1_to_5_delta"] == pytest.approx(-0.2)


def test_sensitivity_report_uses_actual_threshold_labels() -> None:
    report = _sensitivity_report(
        run_id="sensitivity-0-6",
        source_run_id="confirmed-0-995",
        threshold=0.6,
        source_threshold=0.995,
        threshold_metrics=pd.DataFrame([{"split": "test"}]),
        evidence_delta=pd.DataFrame(
            [
                {
                    "source_aggregation_status": "low_confidence_excluded",
                    "sensitivity_aggregation_status": "accepted_directional",
                }
            ]
        ),
        cell_comparison=pd.DataFrame(
            [
                {
                    "canonical_string_name": "Yonex BG80",
                    "aspect": "control",
                    "accepted_evidence_added": 1,
                    "normalized_score_0_to_1_confirmed": 0.8,
                    "normalized_score_0_to_1_sensitivity": 0.75,
                    "normalized_score_delta": -0.05,
                }
            ]
        ),
        profile_v9_summary=pd.DataFrame([{"profile_id": "control"}]),
        profile_threshold_summary=pd.DataFrame([{"profile_id": "control"}]),
    )

    assert "Largest 0.6 versus confirmed 0.995" in report
    assert "Fixed profiles: 0.6 versus current V9" in report
    assert "The `0.6` result remains" in report


def test_fixed_profile_summary_reports_rank_and_top_list_changes() -> None:
    rankings = pd.DataFrame(
        [
            {
                "profile_id": "attacking",
                "matrix": matrix,
                "rank": rank,
                "catalog_id": catalog_id,
                "string_name": catalog_id,
                "final_score": score,
            }
            for matrix, values in (
                ("current_v9", ((1, "a", 0.8), (2, "b", 0.7))),
                ("macbert_candidate", ((1, "b", 0.82), (2, "a", 0.75))),
            )
            for rank, catalog_id, score in values
        ]
    )

    movements, summary = summarize_profile_movements(rankings)

    assert summary.iloc[0]["top1_changed"]
    assert summary.iloc[0]["top5_overlap"] == 2
    assert (
        movements.loc[
            movements["catalog_id"].eq("b"), "rank_improvement_candidate"
        ].iloc[0]
        == 1
    )


def test_profile_audit_reports_near_ties_and_catalog_coverage() -> None:
    rankings = pd.DataFrame(
        [
            {
                "profile_id": profile_id,
                "matrix": "macbert_candidate",
                "rank": rank,
                "catalog_id": catalog_id,
                "string_name": catalog_id,
                "final_score": score,
            }
            for profile_id, values in (
                ("control", ((1, "a", 0.8000), (2, "b", 0.7999), (3, "c", 0.7))),
                ("attack", ((1, "b", 0.9), (2, "c", 0.8), (3, "a", 0.7))),
            )
            for rank, catalog_id, score in values
        ]
    )

    outcomes, coverage = build_profile_audit(rankings)

    control = outcomes[outcomes["profile_id"].eq("control")].iloc[0]
    assert control["descriptive_near_tie"]
    assert control["top3_catalog_ids"] == "a|b|c"
    assert set(coverage["catalog_id"]) == {"a", "b", "c"}
    assert coverage["appears_in_top5"].all()


def test_system_catalog_snapshot_must_match_approved_cohort(tmp_path: Path) -> None:
    snapshot = tmp_path / "catalog.json"
    snapshot.write_text(
        json.dumps(
            {
                "schema_version": "stringsense.recommendation-catalog-snapshot.v1",
                "catalog": [
                    {"catalog_id": "a", "official_performance": None},
                    {"catalog_id": "b", "official_performance": None},
                ],
            }
        ),
        encoding="utf-8",
    )

    payload, facts = load_system_catalog_snapshot(snapshot, {"a", "b"})

    assert payload["schema_version"].endswith(".v1")
    assert set(facts) == {"a", "b"}


def test_low_confidence_stays_visible_but_does_not_change_candidate_score() -> None:
    evidence = pd.DataFrame(
        [
            {
                "canonical_string_name": "Yonex BG80",
                "aspect": "control",
                "review_id": "R1",
                "predicted_label": "positive",
                "confidence": 0.90,
            },
            {
                "canonical_string_name": "Yonex BG80",
                "aspect": "control",
                "review_id": "R2",
                "predicted_label": "negative",
                "confidence": 0.60,
            },
            {
                "canonical_string_name": "Yonex BG80",
                "aspect": "control",
                "review_id": "R3",
                "predicted_label": "not_mentioned",
                "confidence": 0.95,
            },
        ]
    )

    marked = mark_aggregation_status(evidence, threshold=0.80)
    cells = aggregate_candidate_cells(marked)
    coverage = minimum_evidence_analysis(cells, candidates=(1, 2))

    assert marked["aggregation_status"].tolist() == [
        "accepted_directional",
        "low_confidence_excluded",
        "not_mentioned_excluded",
    ]
    assert cells.iloc[0]["accepted_evidence_count"] == 1
    assert cells.iloc[0]["score_1_to_5"] == 5.0
    assert choose_minimum_evidence(coverage) == 1
