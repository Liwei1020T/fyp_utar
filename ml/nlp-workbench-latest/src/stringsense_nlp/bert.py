from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .boundary import RUN_SCHEMA_VERSION
from .boundary import artifact_records
from .boundary import assert_inputs_unchanged
from .boundary import assert_zero_leakage
from .boundary import create_stage_directory
from .boundary import fingerprint_inputs
from .boundary import fingerprint_protected_assets
from .boundary import leakage_report
from .boundary import read_json
from .boundary import resolve_workbench
from .boundary import run_root
from .boundary import runtime_versions
from .boundary import sha256_file
from .boundary import utc_now
from .boundary import write_json_exclusive
from .foundation import load_string_mappings
from .foundation import normalize_string_name
from .labeling import build_label_datasets
from .labeling import load_dictionary_and_rules


BERT_SCHEMA_VERSION = "stringsense.bert-pseudo-labels.v2"
BERT_LABELS = ("not_mentioned", "positive", "negative")
LABEL_POLICY = "high_confidence_silver_three_class"
BASELINE_MODEL_NAME = "google-bert/bert-base-chinese"
PRIMARY_MODEL_NAME = "hfl/chinese-macbert-base"
EXCLUDED_SILVER_LABELS = {"mentioned", "mixed"}
ASPECT_DISPLAY_NAMES = {
    "attack": "攻击性与弹射",
    "comfort": "舒适度",
    "control": "控制",
    "durability": "耐久性",
    "elasticity": "弹性",
    "sound": "击球声音",
    "string_movement": "走线",
    "tension_retention": "保磅性",
    "value_for_money": "性价比",
}


def format_bert_model_input(
    canonical_string_name: str,
    aspect: str,
    review_text: str,
) -> str:
    if aspect not in ASPECT_DISPLAY_NAMES:
        raise ValueError(f"Unsupported BERT aspect: {aspect}")
    if not canonical_string_name.strip() or not review_text.strip():
        raise ValueError("BERT string name and review text cannot be blank")
    return (
        f"目标球线：{canonical_string_name}\n"
        f"评价方面：{ASPECT_DISPLAY_NAMES[aspect]}\n"
        f"评论：{review_text}"
    )


def _canonical_name_index(mappings: pd.DataFrame) -> dict[str, str]:
    confirmed = mappings[mappings["review_status"] == "confirmed"]
    return dict(
        zip(
            confirmed["normalized_name"].astype(str),
            confirmed["canonical_name"].astype(str),
            strict=True,
        )
    )


def load_bert_string_cohort(path: Path) -> tuple[str, ...]:
    cohort = pd.read_csv(path, keep_default_na=False)
    if list(cohort.columns) != ["catalog_id", "canonical_string_name"]:
        raise ValueError(
            "System string cohort must contain catalog_id and canonical_string_name"
        )
    catalog_ids = tuple(cohort["catalog_id"].astype(str).str.strip())
    names = tuple(cohort["canonical_string_name"].astype(str).str.strip())
    if (
        len(names) != 12
        or len(set(names)) != 12
        or len(set(catalog_ids)) != 12
        or any(not value for value in (*catalog_ids, *names))
    ):
        raise ValueError(
            "System string cohort must contain 12 unique non-blank strings"
        )
    return names


def filter_bert_string_cohort(
    dataset: pd.DataFrame,
    canonical_names: tuple[str, ...],
) -> pd.DataFrame:
    available = set(dataset["canonical_string_name"].astype(str))
    missing = sorted(set(canonical_names).difference(available))
    if missing:
        raise ValueError(
            f"BERT string cohort names are missing from the data: {missing}"
        )
    return (
        dataset[dataset["canonical_string_name"].isin(canonical_names)]
        .copy()
        .sort_values("sample_id")
        .reset_index(drop=True)
    )


def build_bert_pseudo_dataset(
    silver: pd.DataFrame,
    mappings: pd.DataFrame,
) -> pd.DataFrame:
    required = (
        "sample_id",
        "split",
        "split_group_id",
        "review_id",
        "string_name",
        "review_text",
        "aspect",
        "label_text",
        "needs_manual_review",
    )
    missing = sorted(set(required).difference(silver.columns))
    if missing:
        raise ValueError(f"Silver dataset is missing BERT columns: {missing}")

    dataset = silver[list(required)].copy()
    canonical_index = _canonical_name_index(mappings)
    dataset["canonical_string_name"] = dataset["string_name"].map(
        lambda value: canonical_index.get(normalize_string_name(value), "")
    )
    unresolved = sorted(
        dataset.loc[dataset["canonical_string_name"] == "", "string_name"].unique()
    )
    if unresolved:
        raise ValueError(f"BERT preparation has unresolved string names: {unresolved}")

    dataset["source_silver_label"] = dataset["label_text"].astype(str)
    unsupported_labels = sorted(
        set(dataset["source_silver_label"]) - set(BERT_LABELS) - EXCLUDED_SILVER_LABELS
    )
    if unsupported_labels:
        raise ValueError(f"Unsupported Silver labels for BERT: {unsupported_labels}")
    dataset["pseudo_label_confidence"] = dataset["needs_manual_review"].map(
        {0: "high", 1: "low"}
    )
    if dataset["pseudo_label_confidence"].isna().any():
        raise ValueError("needs_manual_review must contain only 0 or 1")
    dataset = dataset[
        (dataset["pseudo_label_confidence"] == "high")
        & dataset["source_silver_label"].isin(BERT_LABELS)
    ].copy()
    dataset["bert_label"] = dataset["source_silver_label"]
    label_ids = {label: index for index, label in enumerate(BERT_LABELS)}
    dataset["bert_label_id"] = dataset["bert_label"].map(label_ids).astype(int)
    dataset["annotation_provenance"] = "rule_based_silver_not_human_gold"
    dataset["human_gold"] = False
    aspect_names = dataset["aspect"].map(ASPECT_DISPLAY_NAMES)
    if aspect_names.isna().any():
        raise ValueError("BERT dataset contains an unsupported aspect")
    dataset["model_input"] = [
        format_bert_model_input(name, aspect, text)
        for name, aspect, text in zip(
            dataset["canonical_string_name"].astype(str),
            dataset["aspect"].astype(str),
            dataset["review_text"].astype(str),
            strict=True,
        )
    ]
    columns = [
        "sample_id",
        "split",
        "split_group_id",
        "review_id",
        "string_name",
        "canonical_string_name",
        "aspect",
        "review_text",
        "source_silver_label",
        "bert_label",
        "bert_label_id",
        "needs_manual_review",
        "pseudo_label_confidence",
        "annotation_provenance",
        "human_gold",
        "model_input",
    ]
    return dataset[columns].sort_values("sample_id").reset_index(drop=True)


def validate_bert_pseudo_dataset(dataset: pd.DataFrame) -> dict[str, object]:
    if dataset.empty:
        raise ValueError("BERT dataset cannot be empty")
    if set(dataset["bert_label"]) - set(BERT_LABELS):
        raise ValueError("BERT dataset contains an invalid label")
    manual_review_flags = pd.to_numeric(dataset["needs_manual_review"], errors="coerce")
    if (
        not dataset["pseudo_label_confidence"].eq("high").all()
        or not manual_review_flags.eq(0).all()
    ):
        raise ValueError("BERT dataset must contain high-confidence Silver rows only")
    expected_ids = {label: index for index, label in enumerate(BERT_LABELS)}
    actual_ids = pd.to_numeric(dataset["bert_label_id"], errors="coerce")
    if not actual_ids.eq(dataset["bert_label"].map(expected_ids)).all():
        raise ValueError("BERT label IDs do not match the declared schema")
    if dataset["model_input"].astype(str).str.strip().eq("").any():
        raise ValueError("BERT model_input cannot be blank")
    if dataset["human_gold"].astype(str).str.casefold().isin({"true", "1"}).any():
        raise ValueError("Pseudo-labeled BERT data cannot claim human Gold provenance")

    leakage = leakage_report(dataset)
    assert_zero_leakage(leakage)
    return {
        "schema_version": BERT_SCHEMA_VERSION,
        "label_policy": LABEL_POLICY,
        "rows": int(len(dataset)),
        "reviews": int(dataset["review_id"].nunique()),
        "strings": int(dataset["canonical_string_name"].nunique()),
        "canonical_strings": sorted(dataset["canonical_string_name"].unique()),
        "aspects": int(dataset["aspect"].nunique()),
        "split_counts": {
            str(key): int(value)
            for key, value in dataset["split"].value_counts().sort_index().items()
        },
        "label_distribution": {
            str(key): int(value)
            for key, value in dataset["bert_label"].value_counts().items()
        },
        "confidence_distribution": {
            str(key): int(value)
            for key, value in dataset["pseudo_label_confidence"].value_counts().items()
        },
        "leakage": leakage,
        "human_gold": False,
        "evaluation_status": "pseudo_label_validation_only",
    }


def default_training_config(model_name: str, seed: int) -> dict[str, object]:
    return {
        "schema_version": "stringsense.bert-training-config.v2",
        "model_name": model_name,
        "model_role": "baseline" if model_name == BASELINE_MODEL_NAME else "primary",
        "baseline_model_name": BASELINE_MODEL_NAME,
        "primary_model_name": PRIMARY_MODEL_NAME,
        "task": "aspect_conditioned_three_class_sequence_classification",
        "label_policy": LABEL_POLICY,
        "labels": list(BERT_LABELS),
        "max_length": 256,
        "learning_rate": 2e-5,
        "epochs": 3,
        "train_batch_size": 8,
        "eval_batch_size": 16,
        "weight_decay": 0.01,
        "early_stopping_patience": 2,
        "class_balancing": "inverse_frequency_weighted_cross_entropy",
        "seed": seed,
        "precision": "float32",
        "promotion": {"status": "not_promoted"},
    }


def run_bert_preparation(
    run_id: str,
    model_name: str = PRIMARY_MODEL_NAME,
    seed: int = 42,
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    stage_dir = create_stage_directory(workbench, run_id, "bert")

    raw_data = read_json(before_path := workbench / before["raw_reviews"]["path"])
    if not isinstance(raw_data.get("strings"), list):
        raise ValueError(f"Raw review source has no strings array: {before_path}")
    dictionary, rules = load_dictionary_and_rules(workbench)
    silver, _ = build_label_datasets(raw_data, dictionary, rules)
    mapping_path = workbench / "config/string_name_aliases.csv"
    mappings = load_string_mappings(mapping_path)
    dataset = build_bert_pseudo_dataset(silver, mappings)
    cohort_path = workbench.parents[1] / "config/approved_string_cohort_v1.csv"
    cohort = load_bert_string_cohort(cohort_path)
    dataset = filter_bert_string_cohort(dataset, cohort)
    report = validate_bert_pseudo_dataset(dataset)
    config = default_training_config(model_name, seed)

    dataset_path = stage_dir / "bert_pseudo_labeled_dataset.csv"
    report_path = stage_dir / "bert_dataset_report.json"
    config_path = stage_dir / "bert_training_config.json"
    dataset.to_csv(dataset_path, index=False, encoding="utf-8-sig")
    write_json_exclusive(report_path, report)
    write_json_exclusive(config_path, config)

    assert_inputs_unchanged(before, fingerprint_inputs(workbench))
    assert_inputs_unchanged(
        protected_before,
        fingerprint_protected_assets(workbench),
    )
    artifacts = (dataset_path, report_path, config_path)
    manifest: dict[str, Any] = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "bert",
        "status": "prepared_not_trained",
        "created_at": utc_now(),
        "inputs": before,
        "string_mapping": {
            "path": mapping_path.relative_to(workbench).as_posix(),
            "sha256": sha256_file(mapping_path),
        },
        "string_cohort": {
            "path": cohort_path.relative_to(workbench, walk_up=True).as_posix(),
            "sha256": sha256_file(cohort_path),
            "canonical_strings": list(cohort),
        },
        "dataset": report,
        "training_config": config,
        "runtime_versions": runtime_versions(
            ("pandas", "numpy", "scikit-learn", "torch", "transformers", "accelerate")
        ),
        "artifacts": artifact_records(artifacts, run_root(workbench, run_id)),
        "promotion": {"status": "not_promoted"},
        "gold_dataset_status": "not_available",
        "label_provenance": "rule_based_silver_not_human_gold",
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    write_json_exclusive(
        run_root(workbench, run_id) / "run_manifest.json",
        {**manifest, "stage_manifest": "bert/manifest.json"},
    )
    return {
        "run_id": run_id,
        "status": manifest["status"],
        "dataset_path": str(dataset_path),
        "dataset_sha256": sha256_file(dataset_path),
        "report": report,
        "promotion": manifest["promotion"],
    }
