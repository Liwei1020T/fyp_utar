from __future__ import annotations

from collections import defaultdict
import json
from pathlib import Path
import re
from typing import Any

import jieba
import numpy as np
import pandas as pd

from .boundary import RUN_SCHEMA_VERSION
from .boundary import artifact_records
from .boundary import assert_inputs_unchanged
from .boundary import assert_zero_leakage
from .boundary import create_stage_directory
from .boundary import deterministic_split
from .boundary import fingerprint_inputs
from .boundary import fingerprint_protected_assets
from .boundary import leakage_report
from .boundary import resolve_workbench
from .boundary import review_text_group_id
from .boundary import run_root
from .boundary import runtime_versions
from .boundary import utc_now
from .boundary import write_json_exclusive


def load_dictionary_and_rules(
    workbench: Path,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dictionary = pd.read_csv(workbench / "data/domain_dictionary_optimized_v8.csv")
    rules = pd.read_csv(workbench / "data/normalization_rules_v8.csv")
    return dictionary, rules


def build_normalizer(rules: pd.DataFrame):
    compiled_rules = [
        (str(row.pattern), str(row.replacement))
        for row in rules.itertuples(index=False)
    ]

    def normalize_text(text: str) -> str:
        normalized = str(text)
        for pattern, replacement in compiled_rules:
            normalized = re.sub(pattern, replacement, normalized)
        return re.sub(r"\s+", " ", normalized).strip()

    return normalize_text


def split_into_clauses(text: str) -> list[str]:
    parts = re.split(r"[。！？；;.!?\n]+|但是|但|不过|然而|就是|而且|同时", text)
    return [part.strip(" ，,：:、 ") for part in parts if part.strip(" ，,：:、 ")]


def build_aspect_lexicon(
    dictionary: pd.DataFrame,
) -> dict[str, dict[str, set[str]]]:
    lexicon: defaultdict[str, dict[str, set[str]]] = defaultdict(
        lambda: {
            "aspect_terms": set(),
            "positive_terms": set(),
            "negative_terms": set(),
        }
    )
    for row in dictionary.itertuples(index=False):
        aspect = str(row.aspect).strip()
        term_type = str(row.term_type).strip()
        term = str(row.term).strip()
        polarity = str(row.polarity).strip().lower()
        if not aspect or not term or term == "nan":
            continue
        if term_type == "aspect_term":
            lexicon[aspect]["aspect_terms"].add(term)
        if polarity == "positive":
            lexicon[aspect]["positive_terms"].add(term)
        elif polarity == "negative":
            lexicon[aspect]["negative_terms"].add(term)
    return dict(lexicon)


def _non_overlapping_term_hits(
    text: str,
    terms_by_kind: dict[str, set[str]],
) -> list[tuple[str, str]]:
    candidates: list[tuple[int, int, str, str]] = []
    for kind, terms in terms_by_kind.items():
        for term in terms:
            if not term:
                continue
            start = 0
            while True:
                index = text.find(term, start)
                if index < 0:
                    break
                candidates.append((index, index + len(term), kind, term))
                start = index + 1

    # ponytail: per-term substring scan; use a trie if the dictionary grows materially.
    candidates.sort(key=lambda hit: (-(hit[1] - hit[0]), hit[0], hit[2], hit[3]))
    selected: list[tuple[int, int, str, str]] = []
    for candidate in candidates:
        start, end, _, _ = candidate
        if any(
            start < selected_end and selected_start < end
            for selected_start, selected_end, _, _ in selected
        ):
            continue
        selected.append(candidate)
    return [(kind, term) for _, _, kind, term in selected]


def register_custom_terms(dictionary: pd.DataFrame) -> None:
    for term in dictionary["term"].dropna().astype(str).str.strip():
        if term:
            jieba.add_word(term)


def classify_review_aspect(
    clauses: list[str],
    lexicon: dict[str, set[str]],
) -> dict[str, int | float]:
    positive_hits = 0
    negative_hits = 0
    matched_clauses = 0
    for clause in clauses:
        aspect_hits = _non_overlapping_term_hits(
            clause,
            {"aspect": lexicon["aspect_terms"]},
        )
        polarity_hits = _non_overlapping_term_hits(
            clause,
            {
                "positive": lexicon["positive_terms"],
                "negative": lexicon["negative_terms"],
            },
        )
        clause_positive_hits = sum(
            polarity == "positive" for polarity, _ in polarity_hits
        )
        clause_negative_hits = sum(
            polarity == "negative" for polarity, _ in polarity_hits
        )
        if aspect_hits or clause_positive_hits or clause_negative_hits:
            matched_clauses += 1
            positive_hits += clause_positive_hits
            negative_hits += clause_negative_hits

    if matched_clauses == 0:
        return _classification("not_mentioned", 0, 0, np.nan, 0)
    if positive_hits == 0 and negative_hits == 0:
        return _classification("mentioned", 1, 1, np.nan, 1)
    if positive_hits > 0 and negative_hits == 0:
        return _classification("positive", 2, 1, 1.0, 0)
    if negative_hits > 0 and positive_hits == 0:
        return _classification("negative", 3, 1, -1.0, 0)
    return _classification("mixed", 4, 1, 0.0, 1)


def _classification(
    label_text: str,
    label_id: int,
    mention_flag: int,
    sentiment_id: float,
    needs_manual_review: int,
) -> dict[str, int | float]:
    return {
        "label_text": label_text,
        "label_id": label_id,
        "mention_flag": mention_flag,
        "sentiment_id": sentiment_id,
        "needs_manual_review": needs_manual_review,
    }


def _has_tension_mention(text: str) -> str:
    pattern = r"\b\d{1,2}\s*(?:lbs?|LB|磅)\b|[0-9]{1,2}\s*磅"
    return "yes" if re.search(pattern, text, flags=re.IGNORECASE) else "no"


def _extract_tension(text: str) -> float:
    match = re.search(
        r"([1-4]?\d(?:\.\d)?)\s*(?:lbs?|LB|磅)",
        text,
        flags=re.IGNORECASE,
    )
    return float(match.group(1)) if match else np.nan


def _has_price_mention(text: str) -> str:
    pattern = r"\bRM\s*\d+|\d+\s*rm|价格|价位|贵|便宜|小贵|偏贵|不值|值这个价"
    return "yes" if re.search(pattern, text, flags=re.IGNORECASE) else "no"


def _load_raw_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), list):
        raise ValueError("Raw review source must contain a top-level strings array")
    return payload


def _review_id(value: object) -> str:
    raw = str(value or "").strip()
    if not raw:
        raise ValueError("Every raw review must have a stable review_id")
    return raw if raw.startswith("R") else f"R{raw}"


def build_label_datasets(
    raw_data: dict[str, Any],
    dictionary: pd.DataFrame,
    rules: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    normalizer = build_normalizer(rules)
    lexicon = build_aspect_lexicon(dictionary)
    register_custom_terms(dictionary)
    aspects = sorted(lexicon)
    rows: list[dict[str, object]] = []
    seen_review_ids: set[str] = set()

    for string_index, item in enumerate(raw_data["strings"], start=1):
        string_name = str(item.get("name") or "").strip()
        string_id = f"S{string_index:03d}"
        for review in item.get("reviews", []):
            review_text = str(review.get("content") or "").strip()
            if not review_text:
                continue
            review_id = _review_id(review.get("review_id"))
            if review_id in seen_review_ids:
                raise ValueError(f"Duplicate raw review_id: {review_id}")
            seen_review_ids.add(review_id)

            normalized_text = normalizer(review_text)
            clauses = split_into_clauses(normalized_text)
            group_id = review_text_group_id(normalized_text)
            split = deterministic_split(group_id)
            common = {
                "split": split,
                "split_group_id": group_id,
                "review_id": review_id,
                "string_id": string_id,
                "string_name": string_name,
                "review_text": normalized_text,
                "rating_label": review.get("rating_label", ""),
                "has_tension_mention": _has_tension_mention(normalized_text),
                "has_price_mention": _has_price_mention(normalized_text),
                "extracted_tension": _extract_tension(normalized_text),
                "likes_count": review.get("likes", 0) or 0,
                "review_date": review.get("review_date", ""),
                "source_url": review.get("source_url", ""),
            }
            for aspect in aspects:
                classification = classify_review_aspect(clauses, lexicon[aspect])
                rows.append(
                    {
                        "sample_id": f"{review_id}_{aspect}",
                        **common,
                        "aspect": aspect,
                        **classification,
                    }
                )

    long_dataset = pd.DataFrame(rows)
    high_confidence = long_dataset[
        (long_dataset["needs_manual_review"] == 0)
        & long_dataset["label_text"].isin(["not_mentioned", "positive", "negative"])
    ].copy()
    return long_dataset, high_confidence


def run_labeling(run_id: str, start: Path | None = None) -> dict[str, object]:
    workbench = resolve_workbench(start)
    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    stage_dir = create_stage_directory(workbench, run_id, "labeling")
    raw_data = _load_raw_data(
        workbench / "data/archive_latest/badminton_strings_data.json"
    )
    dictionary, rules = load_dictionary_and_rules(workbench)
    long_dataset, high_confidence = build_label_datasets(raw_data, dictionary, rules)

    long_report = leakage_report(long_dataset)
    high_report = leakage_report(high_confidence)
    assert_zero_leakage(long_report)
    assert_zero_leakage(high_report)

    long_path = stage_dir / "nlp_absa_long_dataset.csv"
    high_path = stage_dir / "nlp_absa_high_confidence.csv"
    long_dataset.to_csv(long_path, index=False, encoding="utf-8-sig")
    high_confidence.to_csv(high_path, index=False, encoding="utf-8-sig")

    after = fingerprint_inputs(workbench)
    assert_inputs_unchanged(before, after)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(protected_before, protected_after)
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "labeling",
        "status": "completed",
        "created_at": utc_now(),
        "split_strategy": {
            "group": "sha256(normalized_review_text)",
            "assignment": "sha256(group_id) modulo 100",
            "thresholds": {"train": 80, "val": 10, "test": 10},
        },
        "inputs": before,
        "protected_assets": protected_before,
        "dataset": {
            "strings": int(len(raw_data["strings"])),
            "reviews": int(long_dataset["review_id"].nunique()),
            "aspects": int(long_dataset["aspect"].nunique()),
            "long_rows": int(len(long_dataset)),
            "high_confidence_rows": int(len(high_confidence)),
            "long_label_distribution": {
                str(key): int(value)
                for key, value in long_dataset["label_text"].value_counts().items()
            },
            "high_label_distribution": {
                str(key): int(value)
                for key, value in high_confidence["label_text"].value_counts().items()
            },
        },
        "leakage": {"long": long_report, "high_confidence": high_report},
        "runtime_versions": runtime_versions(("pandas", "numpy", "jieba")),
        "artifacts": artifact_records(
            (long_path, high_path), run_root(workbench, run_id)
        ),
    }
    manifest_path = stage_dir / "manifest.json"
    write_json_exclusive(manifest_path, manifest)
    return {
        "run_id": run_id,
        "stage_dir": str(stage_dir),
        "manifest_path": str(manifest_path),
        "long_dataset_path": str(long_path),
        "high_confidence_path": str(high_path),
        "leakage": manifest["leakage"],
        "dataset": manifest["dataset"],
    }
