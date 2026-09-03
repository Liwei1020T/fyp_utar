from __future__ import annotations

import hashlib
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np
import pandas as pd

from .bert import ASPECT_DISPLAY_NAMES
from .bert import BERT_LABELS
from .bert import format_bert_model_input
from .bert import load_bert_string_cohort
from .boundary import RUN_SCHEMA_VERSION
from .boundary import artifact_records
from .boundary import assert_inputs_unchanged
from .boundary import create_stage_directory
from .boundary import fingerprint_inputs
from .boundary import fingerprint_protected_assets
from .boundary import read_json
from .boundary import resolve_workbench
from .boundary import run_root
from .boundary import runtime_versions
from .boundary import sha256_file
from .boundary import utc_now
from .boundary import write_json_exclusive
from .foundation import load_string_mappings
from .foundation import normalize_string_name
from .labeling import build_normalizer


INFERENCE_SCHEMA_VERSION = "stringsense.bert-inference.v1"
THRESHOLD_CANDIDATES = (0.70, 0.80, 0.90, 0.95, 0.97, 0.98, 0.99, 0.995)
MINIMUM_EVIDENCE_CANDIDATES = (3, 5, 10, 20)
MAX_DIRECTIONAL_SILVER_ERROR_RATE = 0.01
MIN_DIRECTIONAL_SILVER_RECALL = 0.90
MIN_MATRIX_CELL_COVERAGE = 0.90


def load_inference_catalog(path: Path) -> pd.DataFrame:
    names = load_bert_string_cohort(path)
    catalog = pd.read_csv(path, keep_default_na=False)
    catalog["catalog_id"] = catalog["catalog_id"].astype(str).str.strip()
    catalog["canonical_string_name"] = names
    return catalog


def validate_inference_request(
    canonical_string_name: str,
    aspect: str,
    review_text: str,
    catalog: pd.DataFrame,
) -> str:
    names = set(catalog["canonical_string_name"])
    if canonical_string_name not in names:
        raise ValueError(
            f"String is outside the approved 12-string cohort: {canonical_string_name}"
        )
    return format_bert_model_input(canonical_string_name, aspect, review_text)


def normalize_inference_review(workbench: Path, review_text: str) -> str:
    rules = pd.read_csv(workbench / "data/normalization_rules_v8.csv")
    return build_normalizer(rules)(review_text)


def build_inference_frame(
    dataset: pd.DataFrame,
    catalog: pd.DataFrame,
    dataset_run_id: str,
) -> pd.DataFrame:
    required = {
        "review_id",
        "split",
        "split_group_id",
        "string_name",
        "canonical_string_name",
        "review_text",
        "sample_id",
        "bert_label",
    }
    missing = sorted(required.difference(dataset.columns))
    if missing:
        raise ValueError(f"Inference dataset is missing columns: {missing}")

    review_columns = [
        "review_id",
        "split",
        "split_group_id",
        "string_name",
        "canonical_string_name",
        "review_text",
    ]
    reviews = dataset[review_columns].drop_duplicates()
    if reviews["review_id"].duplicated().any():
        raise ValueError("One review_id maps to multiple inference inputs")
    approved = set(catalog["canonical_string_name"])
    if set(reviews["canonical_string_name"]) != approved:
        raise ValueError("Inference reviews must cover the approved 12-string cohort")

    aspects = pd.DataFrame({"aspect": tuple(ASPECT_DISPLAY_NAMES)})
    frame = reviews.merge(aspects, how="cross")
    frame["source_sample_id"] = frame["review_id"] + "_" + frame["aspect"]
    silver = dataset[["sample_id", "bert_label"]].rename(
        columns={"sample_id": "source_sample_id", "bert_label": "source_silver_label"}
    )
    frame = frame.merge(silver, on="source_sample_id", how="left")
    frame["source_silver_label"] = frame["source_silver_label"].fillna("")
    frame.insert(0, "source_dataset_run_id", dataset_run_id)
    frame["model_input"] = [
        validate_inference_request(name, aspect, text, catalog)
        for name, aspect, text in zip(
            frame["canonical_string_name"],
            frame["aspect"],
            frame["review_text"],
            strict=True,
        )
    ]
    order = {name: index for index, name in enumerate(catalog["canonical_string_name"])}
    frame["_string_order"] = frame["canonical_string_name"].map(order)
    return (
        frame.sort_values(["_string_order", "review_id", "aspect"])
        .drop(columns="_string_order")
        .reset_index(drop=True)
    )


def _require_inference_dependencies() -> dict[str, Any]:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "BERT dependencies are missing. Run ./scripts/bootstrap.sh."
        ) from exc
    return {
        "torch": torch,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
    }


def _load_model(model_dir: Path, requested_device: str) -> tuple[Any, Any, Any, str]:
    dependencies = _require_inference_dependencies()
    torch = dependencies["torch"]
    if requested_device not in {"auto", "cpu", "mps"}:
        raise ValueError("device must be auto, cpu or mps")
    device = (
        "mps"
        if requested_device == "auto" and torch.backends.mps.is_available()
        else requested_device
    )
    if device == "auto":
        device = "cpu"
    if device == "mps" and not torch.backends.mps.is_available():
        raise ValueError("MPS was requested but is unavailable")

    tokenizer = dependencies["AutoTokenizer"].from_pretrained(
        model_dir, local_files_only=True
    )
    model = dependencies["AutoModelForSequenceClassification"].from_pretrained(
        model_dir, local_files_only=True
    )
    labels = tuple(model.config.id2label[index] for index in range(len(BERT_LABELS)))
    if labels != BERT_LABELS:
        raise ValueError(f"Model label order is incompatible: {labels}")
    model.to(device)
    model.eval()
    return tokenizer, model, torch, device


def predict_probabilities(
    model_dir: Path,
    model_inputs: Iterable[str],
    *,
    batch_size: int = 32,
    max_length: int = 128,
    device: str = "auto",
    progress_every_batches: int = 0,
) -> tuple[np.ndarray, str]:
    if batch_size < 1 or max_length < 1:
        raise ValueError("batch_size and max_length must be positive")
    texts = list(model_inputs)
    if not texts or any(not text.strip() for text in texts):
        raise ValueError("Inference inputs cannot be empty")
    tokenizer, model, torch, resolved_device = _load_model(model_dir, device)
    batches: list[np.ndarray] = []
    with torch.inference_mode():
        for batch_index, start in enumerate(range(0, len(texts), batch_size), start=1):
            encoded = tokenizer(
                texts[start : start + batch_size],
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt",
            )
            encoded = {key: value.to(resolved_device) for key, value in encoded.items()}
            logits = model(**encoded).logits
            batches.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
            if progress_every_batches and batch_index % progress_every_batches == 0:
                completed = min(start + batch_size, len(texts))
                print(f"inference rows: {completed}/{len(texts)}", file=sys.stderr)
    return np.concatenate(batches), resolved_device


def attach_predictions(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
    model_run_id: str,
) -> pd.DataFrame:
    if probabilities.shape != (len(frame), len(BERT_LABELS)):
        raise ValueError("Probability shape does not match inference rows")
    evidence = frame.drop(columns="model_input").copy()
    for index, label in enumerate(BERT_LABELS):
        evidence[f"probability_{label}"] = probabilities[:, index]
    predicted_ids = probabilities.argmax(axis=1)
    evidence["predicted_label"] = [BERT_LABELS[index] for index in predicted_ids]
    evidence["confidence"] = probabilities.max(axis=1)
    evidence["model_run_id"] = model_run_id
    return evidence


def threshold_analysis(
    evidence: pd.DataFrame,
    candidates: Iterable[float] = THRESHOLD_CANDIDATES,
    *,
    split: str = "test",
) -> pd.DataFrame:
    test = evidence[
        (evidence["split"] == split) & (evidence["source_silver_label"] != "")
    ].copy()
    if test.empty:
        raise ValueError(f"Threshold analysis requires held-out Silver {split} rows")
    truth_directional = test["source_silver_label"] != "not_mentioned"
    rows = []
    for threshold in candidates:
        accepted = (test["confidence"] >= threshold) & (
            test["predicted_label"] != "not_mentioned"
        )
        correct = test["predicted_label"] == test["source_silver_label"]
        accepted_count = int(accepted.sum())
        correct_count = int((accepted & correct).sum())
        recovered = int((accepted & correct & truth_directional).sum())
        rows.append(
            {
                "confidence_threshold": float(threshold),
                "silver_test_rows": int(len(test)),
                "silver_directional_rows": int(truth_directional.sum()),
                "accepted_directional_rows": accepted_count,
                "accepted_directional_errors": accepted_count - correct_count,
                "accepted_directional_error_rate": (
                    (accepted_count - correct_count) / accepted_count
                    if accepted_count
                    else 1.0
                ),
                "directional_silver_recall": recovered / int(truth_directional.sum()),
                "all_prediction_coverage": float(
                    (test["confidence"] >= threshold).mean()
                ),
            }
        )
    return pd.DataFrame(rows)


def choose_pilot_threshold(analysis: pd.DataFrame) -> float:
    eligible = analysis[
        (
            analysis["accepted_directional_error_rate"]
            <= MAX_DIRECTIONAL_SILVER_ERROR_RATE
        )
        & (analysis["directional_silver_recall"] >= MIN_DIRECTIONAL_SILVER_RECALL)
    ]
    if eligible.empty:
        raise RuntimeError("No pilot confidence threshold satisfies the fixed policy")
    selected = eligible.sort_values("confidence_threshold").iloc[0]
    return float(selected["confidence_threshold"])


def mark_aggregation_status(evidence: pd.DataFrame, threshold: float) -> pd.DataFrame:
    output = evidence.copy()
    output["aggregation_status"] = np.select(
        [
            output["confidence"] < threshold,
            output["predicted_label"] == "not_mentioned",
        ],
        ["low_confidence_excluded", "not_mentioned_excluded"],
        default="accepted_directional",
    )
    return output


def aggregate_candidate_cells(evidence: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for (name, aspect), group in evidence.groupby(
        ["canonical_string_name", "aspect"], sort=False
    ):
        accepted = group[group["aggregation_status"] == "accepted_directional"]
        positive_weight = float(
            accepted.loc[accepted["predicted_label"] == "positive", "confidence"].sum()
        )
        negative_weight = float(
            accepted.loc[accepted["predicted_label"] == "negative", "confidence"].sum()
        )
        total_weight = positive_weight + negative_weight
        positive_share = positive_weight / total_weight if total_weight else np.nan
        rows.append(
            {
                "canonical_string_name": name,
                "aspect": aspect,
                "total_review_count": int(group["review_id"].nunique()),
                "accepted_evidence_count": int(len(accepted)),
                "positive_evidence_count": int(
                    (accepted["predicted_label"] == "positive").sum()
                ),
                "negative_evidence_count": int(
                    (accepted["predicted_label"] == "negative").sum()
                ),
                "low_confidence_count": int(
                    (group["aggregation_status"] == "low_confidence_excluded").sum()
                ),
                "not_mentioned_count": int(
                    (group["aggregation_status"] == "not_mentioned_excluded").sum()
                ),
                "evidence_coverage": float(len(accepted) / len(group)),
                "positive_confidence_weight": positive_weight,
                "negative_confidence_weight": negative_weight,
                "normalized_score_0_to_1": positive_share,
                "score_1_to_5": 1.0 + (4.0 * positive_share),
            }
        )
    return pd.DataFrame(rows)


def minimum_evidence_analysis(
    cells: pd.DataFrame,
    candidates: Iterable[int] = MINIMUM_EVIDENCE_CANDIDATES,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "minimum_evidence": minimum,
                "available_cells": int(
                    (cells["accepted_evidence_count"] >= minimum).sum()
                ),
                "total_cells": int(len(cells)),
                "cell_coverage": float(
                    (cells["accepted_evidence_count"] >= minimum).mean()
                ),
            }
            for minimum in candidates
        ]
    )


def choose_minimum_evidence(analysis: pd.DataFrame) -> int:
    eligible = analysis[analysis["cell_coverage"] >= MIN_MATRIX_CELL_COVERAGE]
    if eligible.empty:
        raise RuntimeError(
            "No minimum evidence candidate satisfies the coverage policy"
        )
    return int(eligible.sort_values("minimum_evidence").iloc[-1]["minimum_evidence"])


def build_candidate_matrix(
    cells: pd.DataFrame,
    catalog: pd.DataFrame,
    minimum_evidence: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    output = cells.copy()
    enough = output["accepted_evidence_count"] >= minimum_evidence
    output["matrix_status"] = np.where(
        enough, "candidate_available", "insufficient_evidence"
    )
    output.loc[~enough, ["normalized_score_0_to_1", "score_1_to_5"]] = np.nan
    wide = output.pivot(
        index="canonical_string_name", columns="aspect", values="score_1_to_5"
    ).reset_index()
    wide = catalog.merge(wide, on="canonical_string_name", how="left")
    return output, wide[["catalog_id", "canonical_string_name", *ASPECT_DISPLAY_NAMES]]


def build_current_comparison(
    cells: pd.DataFrame,
    current_matrix_path: Path,
    mappings_path: Path,
) -> pd.DataFrame:
    current = pd.read_excel(current_matrix_path)
    mappings = load_string_mappings(mappings_path)
    aliases = {
        row.normalized_name: row.canonical_name
        for row in mappings[mappings["review_status"] == "confirmed"].itertuples()
    }
    current["canonical_string_name"] = current["string_name"].map(
        lambda value: aliases.get(normalize_string_name(value), "")
    )
    approved = set(cells["canonical_string_name"])
    current = current[current["canonical_string_name"].isin(approved)]
    if set(current["canonical_string_name"]) != approved:
        missing = sorted(approved.difference(current["canonical_string_name"]))
        raise ValueError(
            f"Current matrix comparison is missing approved strings: {missing}"
        )

    current_long = current.melt(
        id_vars=["canonical_string_name", "string_id", "string_name"],
        value_vars=list(ASPECT_DISPLAY_NAMES),
        var_name="aspect",
        value_name="current_v9_normalized_score",
    )
    comparison = cells.merge(
        current_long,
        on=["canonical_string_name", "aspect"],
        how="left",
    )
    comparison["candidate_minus_current"] = (
        comparison["normalized_score_0_to_1"]
        - comparison["current_v9_normalized_score"]
    )
    return comparison


def acceptance_sample(evidence: pd.DataFrame) -> pd.DataFrame:
    test = evidence[
        (evidence["split"] == "test") & (evidence["source_silver_label"] != "")
    ].copy()
    test["silver_match"] = test["predicted_label"] == test["source_silver_label"]
    mismatches = (
        test[~test["silver_match"]]
        .sort_values(["aspect", "confidence"], ascending=[True, False])
        .groupby("aspect", sort=False)
        .head(1)
    )
    accepted = (
        test[
            test["silver_match"]
            & (test["aggregation_status"] == "accepted_directional")
        ]
        .sort_values(["aspect", "confidence"], ascending=[True, False])
        .groupby("aspect", sort=False)
        .head(1)
    )
    sample = pd.concat([mismatches, accepted], ignore_index=True)
    sample.insert(0, "acceptance_status", "operational_review_only_not_human_gold")
    return sample


def _model_paths(workbench: Path, model_run_id: str) -> tuple[Path, Path]:
    root = run_root(workbench, model_run_id)
    manifest_path = root / "bert_training/manifest.json"
    model_dir = root / "bert_training/model"
    required = (
        manifest_path,
        model_dir / "model.safetensors",
        model_dir / "config.json",
        model_dir / "tokenizer.json",
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Frozen model run is incomplete: {missing}")
    manifest = read_json(manifest_path)
    if manifest.get("status") != "completed_pseudo_label_training":
        raise ValueError("Model run is not a completed pseudo-label training run")
    if manifest.get("promotion", {}).get("status") != "not_promoted":
        raise ValueError("Offline inference expects an unpromoted model run")
    return model_dir, manifest_path


def predict_one(
    model_run_id: str,
    canonical_string_name: str,
    aspect: str,
    review_text: str,
    *,
    source_review_id: str = "",
    device: str = "auto",
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    catalog = load_inference_catalog(
        workbench.parents[1] / "config/approved_string_cohort_v1.csv"
    )
    normalized_review_text = normalize_inference_review(workbench, review_text)
    model_input = validate_inference_request(
        canonical_string_name, aspect, normalized_review_text, catalog
    )
    model_dir, _ = _model_paths(workbench, model_run_id)
    probabilities, resolved_device = predict_probabilities(
        model_dir, [model_input], device=device
    )
    values = probabilities[0]
    predicted_id = int(values.argmax())
    catalog_id = str(
        catalog.loc[
            catalog["canonical_string_name"] == canonical_string_name, "catalog_id"
        ].iloc[0]
    )
    text_sha256 = hashlib.sha256(review_text.encode("utf-8")).hexdigest()
    sample_id = source_review_id or f"adhoc-{text_sha256[:16]}"
    return {
        "model_run_id": model_run_id,
        "source_ids": {
            "catalog_id": catalog_id,
            "review_id": source_review_id,
            "sample_id": f"{sample_id}_{aspect}",
            "review_text_sha256": text_sha256,
        },
        "canonical_string_name": canonical_string_name,
        "aspect": aspect,
        "probabilities": dict(zip(BERT_LABELS, map(float, values), strict=True)),
        "predicted_label": BERT_LABELS[predicted_id],
        "confidence": float(values[predicted_id]),
        "device": resolved_device,
        "promotion": {"status": "not_promoted"},
    }


def _markdown_report(
    run_id: str,
    model_run_id: str,
    dataset_run_id: str,
    threshold: float,
    minimum_evidence: int,
    threshold_table: pd.DataFrame,
    evidence_table: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    available = int((comparison["matrix_status"] == "candidate_available").sum())
    largest_differences = (
        comparison.dropna(subset=["candidate_minus_current"])
        .assign(
            absolute_difference=lambda frame: frame["candidate_minus_current"].abs()
        )
        .nlargest(10, "absolute_difference")[
            [
                "canonical_string_name",
                "aspect",
                "accepted_evidence_count",
                "normalized_score_0_to_1",
                "current_v9_normalized_score",
                "candidate_minus_current",
            ]
        ]
    )
    return "\n".join(
        [
            "# MacBERT Offline Inference Candidate Report",
            "",
            f"- Run: `{run_id}`",
            f"- Frozen model run: `{model_run_id}`",
            f"- Frozen dataset run: `{dataset_run_id}`",
            f"- Pilot confidence threshold: `{threshold:g}`",
            f"- Pilot minimum evidence: `{minimum_evidence}`",
            f"- Candidate cells available: `{available}/108`",
            "- Promotion: `not_promoted`",
            "",
            "## Decision boundary",
            "",
            "The threshold was selected from held-out Silver agreement and coverage;",
            "it is not human Gold accuracy, probability calibration, or Cohen's Kappa.",
            "Low-confidence predictions remain in the evidence CSV and are excluded",
            "from aggregation. No backend import or protected V9 overwrite occurred.",
            "",
            "## Pilot threshold candidates",
            "",
            "```csv",
            threshold_table.to_csv(index=False).strip(),
            "```",
            "",
            "## Pilot minimum-evidence candidates",
            "",
            "```csv",
            evidence_table.to_csv(index=False).strip(),
            "```",
            "",
            "## Current V9 comparison",
            "",
            "The comparison is review evidence only. It does not authorize promotion.",
            "",
            "```csv",
            largest_differences.to_csv(index=False).strip(),
            "```",
            "",
        ]
    )


def run_inference_pipeline(
    run_id: str,
    model_run_id: str,
    dataset_run_id: str,
    *,
    batch_size: int = 32,
    device: str = "auto",
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    catalog_path = workbench.parents[1] / "config/approved_string_cohort_v1.csv"
    catalog = load_inference_catalog(catalog_path)
    model_dir, model_manifest_path = _model_paths(workbench, model_run_id)
    model_manifest = read_json(model_manifest_path)
    dataset_path = (
        run_root(workbench, dataset_run_id) / "bert/bert_pseudo_labeled_dataset.csv"
    )
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Frozen inference dataset is missing: {dataset_path}")
    dataset_sha256 = sha256_file(dataset_path)
    expected_sha256 = str(model_manifest.get("dataset", {}).get("sha256", ""))
    if dataset_sha256 != expected_sha256:
        raise ValueError(
            f"Frozen dataset SHA256 mismatch: expected {expected_sha256}, received {dataset_sha256}"
        )

    dataset = pd.read_csv(dataset_path, keep_default_na=False)
    frame = build_inference_frame(dataset, catalog, dataset_run_id)
    probabilities, resolved_device = predict_probabilities(
        model_dir,
        frame["model_input"],
        batch_size=batch_size,
        max_length=int(model_manifest["config"]["max_length"]),
        device=device,
        progress_every_batches=50,
    )
    evidence = attach_predictions(frame, probabilities, model_run_id)
    threshold_table = threshold_analysis(evidence)
    threshold = choose_pilot_threshold(threshold_table)
    evidence = mark_aggregation_status(evidence, threshold)
    cells = aggregate_candidate_cells(evidence)
    evidence_table = minimum_evidence_analysis(cells)
    minimum_evidence = choose_minimum_evidence(evidence_table)
    cells, matrix = build_candidate_matrix(cells, catalog, minimum_evidence)
    comparison = build_current_comparison(
        cells,
        workbench / "output/latest_practical_string_feature_matrix_v9_v8dict.xlsx",
        workbench / "config/string_name_aliases.csv",
    )
    sample = acceptance_sample(evidence)

    stage_dir = create_stage_directory(workbench, run_id, "bert_inference")
    paths = {
        "evidence": stage_dir / "macbert_review_aspect_evidence.csv",
        "cells": stage_dir / "candidate_matrix_cells.csv",
        "matrix_csv": stage_dir / "candidate_matrix_12x9.csv",
        "matrix_xlsx": stage_dir / "candidate_matrix_12x9.xlsx",
        "thresholds": stage_dir / "pilot_threshold_analysis.csv",
        "minimum_evidence": stage_dir / "pilot_minimum_evidence_analysis.csv",
        "acceptance": stage_dir / "acceptance_sample_not_gold.csv",
        "comparison": stage_dir / "candidate_vs_current_v9.csv",
        "decision": stage_dir / "pilot_decision.json",
        "report": stage_dir / "report.md",
    }
    evidence.to_csv(paths["evidence"], index=False, encoding="utf-8-sig")
    cells.to_csv(paths["cells"], index=False, encoding="utf-8-sig")
    matrix.to_csv(paths["matrix_csv"], index=False, encoding="utf-8-sig")
    matrix.to_excel(paths["matrix_xlsx"], index=False)
    threshold_table.to_csv(paths["thresholds"], index=False, encoding="utf-8-sig")
    evidence_table.to_csv(paths["minimum_evidence"], index=False, encoding="utf-8-sig")
    sample.to_csv(paths["acceptance"], index=False, encoding="utf-8-sig")
    comparison.to_csv(paths["comparison"], index=False, encoding="utf-8-sig")
    decision = {
        "schema_version": INFERENCE_SCHEMA_VERSION,
        "confidence_threshold": threshold,
        "minimum_evidence": minimum_evidence,
        "selection_policy": {
            "threshold": {
                "candidates": list(THRESHOLD_CANDIDATES),
                "maximum_directional_silver_error_rate": MAX_DIRECTIONAL_SILVER_ERROR_RATE,
                "minimum_directional_silver_recall": MIN_DIRECTIONAL_SILVER_RECALL,
                "selection": "lowest_candidate_meeting_both_constraints",
            },
            "minimum_evidence": {
                "candidates": list(MINIMUM_EVIDENCE_CANDIDATES),
                "minimum_matrix_cell_coverage": MIN_MATRIX_CELL_COVERAGE,
                "selection": "largest_candidate_meeting_coverage_constraint",
            },
        },
        "claim_boundary": "pseudo_label_validation_only_not_human_gold",
        "promotion": {"status": "not_promoted"},
    }
    write_json_exclusive(paths["decision"], decision)
    paths["report"].write_text(
        _markdown_report(
            run_id,
            model_run_id,
            dataset_run_id,
            threshold,
            minimum_evidence,
            threshold_table,
            evidence_table,
            comparison,
        ),
        encoding="utf-8",
    )

    after = fingerprint_inputs(workbench)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(before, after)
    assert_inputs_unchanged(protected_before, protected_after)
    artifacts = artifact_records(paths.values(), run_root(workbench, run_id))
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "bert_inference",
        "status": "completed_candidate_not_promoted",
        "created_at": utc_now(),
        "model": {
            "run_id": model_run_id,
            "manifest_path": model_manifest_path.relative_to(workbench).as_posix(),
            "manifest_sha256": sha256_file(model_manifest_path),
            "weights_sha256": sha256_file(model_dir / "model.safetensors"),
        },
        "dataset": {
            "run_id": dataset_run_id,
            "path": dataset_path.relative_to(workbench).as_posix(),
            "sha256": dataset_sha256,
        },
        "inputs": before,
        "protected_assets": protected_before,
        "configuration": {
            "batch_size": batch_size,
            "max_length": int(model_manifest["config"]["max_length"]),
            "device": resolved_device,
            "cpu_threads": _require_inference_dependencies()["torch"].get_num_threads(),
            "aspects": list(ASPECT_DISPLAY_NAMES),
            **decision,
        },
        "summary": {
            "reviews": int(frame["review_id"].nunique()),
            "prediction_rows": int(len(evidence)),
            "strings": int(evidence["canonical_string_name"].nunique()),
            "aspects": int(evidence["aspect"].nunique()),
            "candidate_cells": int(
                (cells["matrix_status"] == "candidate_available").sum()
            ),
            "low_confidence_rows": int(
                (evidence["aggregation_status"] == "low_confidence_excluded").sum()
            ),
        },
        "runtime_versions": runtime_versions(
            ("pandas", "numpy", "torch", "transformers", "openpyxl")
        ),
        "artifacts": artifacts,
        "promotion": {
            "status": "not_promoted",
            "requires_separate_human_approval": True,
            "canonical_backend_artifact_modified": False,
            "backend_imported": False,
        },
        "gold_dataset_status": "not_available",
        "evaluation_status": "pseudo_label_validation_only",
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(workbench, run_id) / "run_manifest.json",
        {**manifest, "stage_manifest": "bert_inference/manifest.json"},
    )
    return {
        "run_id": run_id,
        "run_root": str(run_root(workbench, run_id)),
        "confidence_threshold": threshold,
        "minimum_evidence": minimum_evidence,
        "summary": manifest["summary"],
        "promotion": manifest["promotion"],
    }
