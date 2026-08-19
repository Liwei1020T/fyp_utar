from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score


ALLOWED_LABELS = (
    "not_mentioned",
    "positive",
    "negative",
    "neutral",
    "mixed",
    "uncertain",
)
ANNOTATION_METADATA_COLUMNS = (
    "annotation_id",
    "sample_number",
    "review_id",
    "raw_string_name",
    "canonical_string_name",
    "language",
    "raw_text",
    "normalized_text",
)
SILVER_DRAFT_LABEL_MAP = {
    "not_mentioned": "not_mentioned",
    "positive": "positive",
    "negative": "negative",
    "mixed": "mixed",
    "mentioned": "neutral",
}


def label_column(aspect: str) -> str:
    return f"{aspect}_label"


def annotation_columns(aspects: Sequence[str]) -> list[str]:
    return [
        "annotation_batch_id",
        "annotator_id",
        *ANNOTATION_METADATA_COLUMNS,
        *[label_column(aspect) for aspect in aspects],
        "annotator_notes",
    ]


def _stable_seed(seed: int, value: str) -> int:
    digest = hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()
    return int(digest[:8], 16)


def _weighted_choice(
    frame: pd.DataFrame,
    size: int,
    seed: int,
) -> list[int]:
    if size <= 0 or frame.empty:
        return []
    if size >= len(frame):
        return frame.index.tolist()
    weights = frame["sampling_weight"].astype(float).to_numpy()
    weights = weights / weights.sum()
    rng = np.random.default_rng(seed)
    return rng.choice(
        frame.index.to_numpy(), size=size, replace=False, p=weights
    ).tolist()


def sampling_weights(
    reviews: pd.DataFrame,
    silver: pd.DataFrame,
) -> pd.Series:
    language_counts = reviews["language"].value_counts().to_dict()
    string_counts = reviews["canonical_string_name"].value_counts().to_dict()
    signal_rows = silver[silver["label_text"] != "not_mentioned"].copy()
    signal_rows["signal"] = (
        signal_rows["aspect"].astype(str) + ":" + signal_rows["label_text"].astype(str)
    )
    signal_counts = signal_rows["signal"].value_counts().to_dict()
    review_signals = signal_rows.groupby("review_id")["signal"].agg(list).to_dict()

    def weight(row: object) -> float:
        review_id = str(getattr(row, "review_id"))
        language = str(getattr(row, "language"))
        string_name = str(getattr(row, "canonical_string_name"))
        value = 1.0
        value += 1.0 / math.sqrt(language_counts[language])
        value += 1.0 / math.sqrt(string_counts[string_name])
        for signal in review_signals.get(review_id, []):
            value += 1.0 / math.sqrt(signal_counts[signal])
        return value

    return pd.Series(
        [weight(row) for row in reviews.itertuples(index=False)],
        index=reviews.index,
        dtype=float,
    )


def stratified_sample(
    reviews: pd.DataFrame,
    silver: pd.DataFrame,
    sample_size: int,
    seed: int,
    per_string_floor: int = 10,
    per_language_floor: int = 1,
) -> pd.DataFrame:
    included = reviews[reviews["cleaning_status"].str.startswith("included")].copy()
    included = included.sort_values("review_id").reset_index(drop=True)
    if sample_size <= 0 or sample_size > len(included):
        raise ValueError("sample_size must be between 1 and the clean review count")
    included["sampling_weight"] = sampling_weights(included, silver).to_numpy()

    selected: list[int] = []
    for string_name, group in included.groupby("canonical_string_name", sort=True):
        quota = min(per_string_floor, len(group))
        selected.extend(
            _weighted_choice(group, quota, _stable_seed(seed, str(string_name)))
        )

    selected = list(dict.fromkeys(selected))
    for language, group in included.groupby("language", sort=True):
        group_indexes = set(group.index)
        already_selected = len(group_indexes.intersection(selected))
        quota = min(per_language_floor, len(group)) - already_selected
        if quota > 0:
            available = group.drop(index=list(group_indexes.intersection(selected)))
            selected.extend(
                _weighted_choice(
                    available,
                    quota,
                    _stable_seed(seed, f"language:{language}"),
                )
            )

    selected = list(dict.fromkeys(selected))
    if len(selected) > sample_size:
        selected = _weighted_choice(
            included.loc[selected],
            sample_size,
            _stable_seed(seed, "floor-trim"),
        )
    elif len(selected) < sample_size:
        remaining = included.drop(index=selected)
        selected.extend(
            _weighted_choice(
                remaining,
                sample_size - len(selected),
                _stable_seed(seed, "remainder"),
            )
        )

    sample = included.loc[selected].copy().reset_index(drop=True)
    sample.insert(0, "sample_number", np.arange(1, len(sample) + 1))
    sample.insert(
        0, "annotation_id", sample["review_id"].map(lambda value: f"GOLD-{value}")
    )
    return sample


def annotation_template(
    sample: pd.DataFrame,
    aspects: Sequence[str],
    annotator_id: str,
    batch_id: str = "gold-pilot-v1",
) -> pd.DataFrame:
    template = sample[
        [
            "annotation_id",
            "sample_number",
            "review_id",
            "raw_string_name",
            "canonical_string_name",
            "language",
            "raw_text",
            "normalized_text",
        ]
    ].copy()
    template.insert(0, "annotator_id", annotator_id)
    template.insert(0, "annotation_batch_id", batch_id)
    for aspect in aspects:
        template[label_column(aspect)] = ""
    template["annotator_notes"] = ""
    return template[annotation_columns(aspects)]


def annotation_schema(aspects: Sequence[str]) -> dict[str, object]:
    return {
        "schema_version": "stringsense.gold-annotation.v1",
        "unit": "one review with one label per aspect",
        "aspects": list(aspects),
        "aspect_display_names": {
            "attack": "Attack / Repulsion",
            "comfort": "Comfort",
            "control": "Control",
            "durability": "Durability",
            "elasticity": "Elasticity",
            "sound": "Sound",
            "string_movement": "String movement",
            "tension_retention": "Tension retention",
            "value_for_money": "Value",
        },
        "allowed_labels": list(ALLOWED_LABELS),
        "required_columns": annotation_columns(aspects),
        "blank_labels_allowed_in_template": True,
        "blank_labels_allowed_for_merge": False,
        "silver_labels_exposed": False,
    }


def _human_annotation_eligible(frame: pd.DataFrame) -> bool:
    annotator_ids = frame["annotator_id"].fillna("").astype(str).str.casefold()
    automated_prefixes = ("ai_", "auto_", "silver_")
    if annotator_ids.str.startswith(automated_prefixes).any():
        return False
    if "annotation_provenance" not in frame:
        return True
    provenance = (
        frame["annotation_provenance"].fillna("").astype(str).str.strip().str.casefold()
    )
    return provenance.isin(("", "human")).all()


def validate_annotation_frame(
    frame: pd.DataFrame,
    aspects: Sequence[str],
    require_complete: bool,
) -> dict[str, object]:
    required = annotation_columns(aspects)
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"Annotation file is missing columns: {missing}")
    if frame["annotation_id"].duplicated().any():
        raise ValueError("Annotation IDs must be unique")

    invalid: list[dict[str, object]] = []
    blanks = 0
    allowed = set(ALLOWED_LABELS)
    for row_number, row in enumerate(frame.itertuples(index=False), start=2):
        for aspect in aspects:
            column = label_column(aspect)
            value = str(getattr(row, column) or "").strip().lower()
            if not value or value == "nan":
                blanks += 1
                if require_complete:
                    invalid.append(
                        {"row": row_number, "column": column, "value": "<blank>"}
                    )
            elif value not in allowed:
                invalid.append({"row": row_number, "column": column, "value": value})
    if invalid:
        raise ValueError(f"Invalid annotation labels: {invalid[:20]}")
    return {
        "rows": int(len(frame)),
        "label_cells": int(len(frame) * len(aspects)),
        "blank_label_cells": blanks,
        "complete": blanks == 0,
        "valid": True,
        "human_annotation_eligible": _human_annotation_eligible(frame),
    }


def build_silver_assisted_draft(
    template: pd.DataFrame,
    silver: pd.DataFrame,
    aspects: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    validate_annotation_frame(template, aspects, require_complete=False)
    required = {"review_id", "aspect", "label_text", "needs_manual_review"}
    missing = sorted(required.difference(silver.columns))
    if missing:
        raise ValueError(f"Silver dataset is missing columns: {missing}")
    relevant = silver[
        silver["review_id"].isin(template["review_id"]) & silver["aspect"].isin(aspects)
    ].copy()
    if relevant.duplicated(["review_id", "aspect"]).any():
        raise ValueError("Silver review-aspect rows must be unique")
    relevant["suggested_label"] = relevant["label_text"].map(SILVER_DRAFT_LABEL_MAP)
    if relevant["suggested_label"].isna().any():
        unknown = sorted(relevant.loc[relevant["suggested_label"].isna(), "label_text"])
        raise ValueError(f"Unsupported Silver labels: {unknown}")
    expected = {
        (review_id, aspect) for review_id in template["review_id"] for aspect in aspects
    }
    actual = set(zip(relevant["review_id"], relevant["aspect"]))
    if actual != expected:
        raise ValueError("Silver dataset does not cover every template review-aspect")

    draft = template.copy()
    draft["annotation_batch_id"] = (
        draft["annotation_batch_id"].astype(str) + "-ai-silver-draft"
    )
    draft["annotator_id"] = "AI_SILVER_DRAFT"
    for aspect in aspects:
        labels = relevant[relevant["aspect"] == aspect].set_index("review_id")[
            "suggested_label"
        ]
        draft[label_column(aspect)] = draft["review_id"].map(labels)
    draft["annotator_notes"] = "AI/Silver-assisted draft; human verification required"
    draft["annotation_provenance"] = "automatic_silver_conversion_not_human"
    draft["human_review_status"] = "pending"

    annotation_ids = template.set_index("review_id")["annotation_id"]
    evidence = relevant[
        ["review_id", "aspect", "label_text", "suggested_label", "needs_manual_review"]
    ].copy()
    evidence.insert(0, "annotation_id", evidence["review_id"].map(annotation_ids))
    evidence["conversion_rule"] = evidence["label_text"].map(
        lambda value: "mentioned_to_neutral" if value == "mentioned" else "identity"
    )
    evidence["annotation_provenance"] = "automatic_silver_conversion_not_human"
    evidence["human_review_status"] = "pending"
    return draft, evidence.sort_values(["annotation_id", "aspect"]).reset_index(
        drop=True
    )


def _normalise_labels(frame: pd.DataFrame, aspects: Sequence[str]) -> pd.DataFrame:
    output = frame.copy()
    for aspect in aspects:
        column = label_column(aspect)
        output[column] = output[column].fillna("").astype(str).str.strip().str.lower()
    return output


def merge_annotations(
    annotator_a: pd.DataFrame,
    annotator_b: pd.DataFrame,
    aspects: Sequence[str],
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object], pd.DataFrame]:
    validation_a = validate_annotation_frame(
        annotator_a, aspects, require_complete=True
    )
    validation_b = validate_annotation_frame(
        annotator_b, aspects, require_complete=True
    )
    if (
        not validation_a["human_annotation_eligible"]
        or not validation_b["human_annotation_eligible"]
    ):
        raise ValueError("Automated annotation drafts cannot be merged as human Gold")
    a = _normalise_labels(annotator_a, aspects).set_index("annotation_id")
    b = _normalise_labels(annotator_b, aspects).set_index("annotation_id")
    if set(a.index) != set(b.index):
        raise ValueError("Annotator files do not contain the same annotation IDs")
    a = a.sort_index()
    b = b.sort_index()
    for column in ANNOTATION_METADATA_COLUMNS[1:]:
        if not a[column].equals(b[column]):
            raise ValueError(f"Annotator metadata differs in column: {column}")

    rows: list[dict[str, object]] = []
    agreement: dict[str, object] = {"per_aspect": {}}
    all_a: list[str] = []
    all_b: list[str] = []
    for aspect in aspects:
        column = label_column(aspect)
        labels_a = a[column].tolist()
        labels_b = b[column].tolist()
        all_a.extend(labels_a)
        all_b.extend(labels_b)
        kappa = cohen_kappa_score(labels_a, labels_b, labels=ALLOWED_LABELS)
        agreement["per_aspect"][aspect] = {
            "rows": len(labels_a),
            "agreement": float(np.mean(np.asarray(labels_a) == np.asarray(labels_b))),
            "cohen_kappa": None if np.isnan(kappa) else float(kappa),
        }
        for annotation_id, label_a, label_b in zip(a.index, labels_a, labels_b):
            rows.append(
                {
                    "annotation_id": annotation_id,
                    "review_id": a.at[annotation_id, "review_id"],
                    "raw_string_name": a.at[annotation_id, "raw_string_name"],
                    "canonical_string_name": a.at[
                        annotation_id, "canonical_string_name"
                    ],
                    "language": a.at[annotation_id, "language"],
                    "raw_text": a.at[annotation_id, "raw_text"],
                    "normalized_text": a.at[annotation_id, "normalized_text"],
                    "aspect": aspect,
                    "annotator_a_label": label_a,
                    "annotator_b_label": label_b,
                    "agrees": label_a == label_b,
                    "resolved_label": label_a if label_a == label_b else "",
                    "adjudicator": "",
                    "adjudication_notes": "",
                }
            )
    overall_kappa = cohen_kappa_score(all_a, all_b, labels=ALLOWED_LABELS)
    agreement["overall"] = {
        "rows": len(all_a),
        "agreement": float(np.mean(np.asarray(all_a) == np.asarray(all_b))),
        "cohen_kappa": None if np.isnan(overall_kappa) else float(overall_kappa),
    }
    merged = pd.DataFrame(rows)
    disagreements = merged[~merged["agrees"]].copy()
    adjudication = merged.copy()
    return merged, disagreements, agreement, adjudication


def build_gold_dataset(
    adjudicated: pd.DataFrame,
    allowed_labels: Iterable[str] = ALLOWED_LABELS,
) -> pd.DataFrame:
    required = {
        "annotation_id",
        "review_id",
        "raw_string_name",
        "canonical_string_name",
        "language",
        "raw_text",
        "normalized_text",
        "aspect",
        "annotator_a_label",
        "annotator_b_label",
        "resolved_label",
        "adjudicator",
        "adjudication_notes",
    }
    missing = sorted(required.difference(adjudicated.columns))
    if missing:
        raise ValueError(f"Adjudication file is missing columns: {missing}")
    allowed = set(allowed_labels)
    resolved = (
        adjudicated["resolved_label"].fillna("").astype(str).str.strip().str.lower()
    )
    invalid = adjudicated.loc[~resolved.isin(allowed), ["review_id", "aspect"]]
    if not invalid.empty:
        raise ValueError(
            "Every review-aspect row needs an allowed resolved_label before Gold export"
        )
    output = adjudicated.copy()
    output["gold_label"] = resolved
    output["was_adjudicated"] = (
        output["annotator_a_label"] != output["annotator_b_label"]
    )
    return output[
        [
            "annotation_id",
            "review_id",
            "raw_string_name",
            "canonical_string_name",
            "language",
            "raw_text",
            "normalized_text",
            "aspect",
            "gold_label",
            "annotator_a_label",
            "annotator_b_label",
            "was_adjudicated",
            "adjudicator",
            "adjudication_notes",
        ]
    ]


def sampling_coverage(
    sample: pd.DataFrame,
    silver: pd.DataFrame,
) -> dict[str, object]:
    review_ids = set(sample["review_id"])
    selected_silver = silver[silver["review_id"].isin(review_ids)]
    weak_distribution = (
        selected_silver.groupby(["aspect", "label_text"]).size().sort_index()
    )
    return {
        "reviews": int(len(sample)),
        "string_distribution": {
            str(key): int(value)
            for key, value in sample["canonical_string_name"].value_counts().items()
        },
        "language_distribution": {
            str(key): int(value)
            for key, value in sample["language"].value_counts().items()
        },
        "weak_label_distribution": {
            f"{aspect}:{label}": int(value)
            for (aspect, label), value in weak_distribution.items()
        },
        "comparison_reviews": int(sample["is_comparison"].sum()),
        "code_mixed_reviews": int(sample["is_code_mixed"].sum()),
    }


def label_distribution(frame: pd.DataFrame, aspects: Sequence[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for aspect in aspects:
        counts.update(frame[label_column(aspect)].dropna().astype(str).str.strip())
    return dict(sorted(counts.items()))


def write_json(path: Path, payload: dict[str, object]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
