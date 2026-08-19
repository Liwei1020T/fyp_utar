from __future__ import annotations

from collections import Counter, defaultdict
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from typing import Any, Mapping
import unicodedata

import pandas as pd

from .annotation import annotation_schema
from .annotation import annotation_template
from .annotation import sampling_coverage
from .annotation import stratified_sample
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
from .boundary import sha256_file
from .boundary import utc_now
from .boundary import write_json_exclusive
from .labeling import build_label_datasets
from .labeling import load_dictionary_and_rules


ASPECTS = (
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
MAPPING_COLUMNS = (
    "raw_name",
    "normalized_name",
    "canonical_name",
    "mapping_method",
    "confidence",
    "review_status",
    "notes",
)
URL_PATTERN = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)
COMPARISON_PATTERN = re.compile(
    r"对比|相比|相较|不如|胜过|(?:\bvs\.?\b)|(?:\bversus\b)|比.{0,12}更",
    re.IGNORECASE,
)


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.saw_tag = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        self.saw_tag = True

    def handle_endtag(self, tag: str) -> None:
        self.saw_tag = True

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def conservative_normalize(value: object) -> tuple[str, list[str]]:
    if not isinstance(value, str):
        return "", []
    text = value
    transformations: list[str] = []
    normalized = unicodedata.normalize("NFKC", text)
    if normalized != text:
        transformations.append("unicode_nfkc")
    decoded = unescape(normalized)
    if decoded != normalized:
        transformations.append("html_unescape")
    parser = _HTMLTextExtractor()
    parser.feed(decoded)
    without_html = "".join(parser.parts)
    if parser.saw_tag:
        decoded = without_html
        transformations.append("html_tags_removed")
    url_replaced = URL_PATTERN.sub("<URL>", decoded)
    if url_replaced != decoded:
        transformations.append("url_replaced")
    cleaned_characters: list[str] = []
    removed_hidden = False
    for character in url_replaced:
        category = unicodedata.category(character)
        if category == "Cf" or (category == "Cc" and character not in "\t\n\r"):
            removed_hidden = True
            continue
        cleaned_characters.append(character)
    if removed_hidden:
        transformations.append("hidden_control_removed")
    cleaned = re.sub(r"\s+", " ", "".join(cleaned_characters)).strip()
    if cleaned != "".join(cleaned_characters):
        transformations.append("whitespace_collapsed")
    return cleaned, transformations


def language_category(text: str) -> str:
    has_zh = bool(re.search(r"[\u3400-\u9fff]", text))
    has_en = bool(re.search(r"[A-Za-z]", text))
    if has_zh and has_en:
        return "mixed_zh_en"
    if has_zh:
        return "zh_only"
    if has_en:
        return "en_only"
    return "other"


def normalize_string_name(value: object) -> str:
    normalized = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return "".join(character for character in normalized if character.isalnum())


def load_string_mappings(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    missing = sorted(set(MAPPING_COLUMNS).difference(frame.columns))
    if missing:
        raise ValueError(f"String mapping config is missing columns: {missing}")
    frame = frame[list(MAPPING_COLUMNS)].copy()
    computed = frame["raw_name"].map(normalize_string_name)
    blank_normalized = frame["normalized_name"].str.strip() == ""
    frame.loc[blank_normalized, "normalized_name"] = computed[blank_normalized]
    if (frame["normalized_name"] != computed).any():
        raise ValueError("normalized_name must match the deterministic name normalizer")
    frame["confidence"] = pd.to_numeric(frame["confidence"], errors="raise")
    if ((frame["confidence"] < 0) | (frame["confidence"] > 1)).any():
        raise ValueError("String mapping confidence must be between 0 and 1")
    allowed_statuses = {"confirmed", "pending", "rejected"}
    if not set(frame["review_status"]).issubset(allowed_statuses):
        raise ValueError(f"review_status must be one of {sorted(allowed_statuses)}")
    confirmed = frame[frame["review_status"] == "confirmed"]
    conflicts = confirmed.groupby("normalized_name")["canonical_name"].nunique()
    if (conflicts > 1).any():
        raise ValueError(
            "One normalized alias maps to multiple confirmed canonical names"
        )
    return frame


def _mapping_index(mappings: pd.DataFrame) -> dict[str, Mapping[str, object]]:
    priority = {"confirmed": 0, "pending": 1, "rejected": 2}
    rows = sorted(
        mappings.to_dict("records"),
        key=lambda row: (
            priority[str(row["review_status"])],
            -float(row["confidence"]),
        ),
    )
    index: dict[str, Mapping[str, object]] = {}
    for row in rows:
        index.setdefault(str(row["normalized_name"]), row)
    return index


def _normalise_review_id(value: object) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return "", ""
    return raw, raw if raw.startswith("R") else f"R{raw}"


def _duplicate_summary(groups: Mapping[str, list[dict[str, object]]]) -> dict[str, int]:
    duplicates = [members for members in groups.values() if len(members) > 1]
    return {
        "groups": len(duplicates),
        "records_in_groups": sum(len(members) for members in duplicates),
        "extra_records": sum(len(members) - 1 for members in duplicates),
        "cross_string_groups": sum(
            len({str(member["raw_string_name"]) for member in members}) > 1
            for members in duplicates
        ),
        "within_string_groups": sum(
            len({str(member["raw_string_name"]) for member in members}) == 1
            for members in duplicates
        ),
    }


def build_clean_reviews(
    raw_data: dict[str, Any],
    mappings: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    mapping_index = _mapping_index(mappings)
    records: list[dict[str, object]] = []
    source_index = 0
    for item in raw_data["strings"]:
        raw_string_name = str(item.get("name") or "").strip()
        normalized_string_name = normalize_string_name(raw_string_name)
        mapping = mapping_index.get(normalized_string_name)
        canonical_name = (
            str(mapping["canonical_name"])
            if mapping and mapping["review_status"] == "confirmed"
            else ""
        )
        mapping_status = str(mapping["review_status"]) if mapping else "pending"
        for review in item.get("reviews", []):
            source_index += 1
            raw_review_id, review_id = _normalise_review_id(review.get("review_id"))
            raw_value = review.get("content")
            raw_text = raw_value if isinstance(raw_value, str) else ""
            normalized_text, transformations = conservative_normalize(raw_value)
            reasons: list[str] = []
            if not raw_review_id:
                reasons.append("missing_review_id")
            if not isinstance(raw_value, str):
                reasons.append("non_string_text")
            elif not normalized_text:
                reasons.append("blank_text_after_normalization")
            split_group_id = (
                review_text_group_id(normalized_text) if normalized_text else ""
            )
            records.append(
                {
                    "source_record_index": source_index,
                    "raw_review_id": raw_review_id,
                    "review_id": review_id,
                    "raw_text": raw_text,
                    "normalized_text": normalized_text,
                    "cleaning_status": "invalid" if reasons else "included",
                    "exclusion_reason": "|".join(reasons),
                    "data_source": "data/archive_latest/badminton_strings_data.json",
                    "source_url": str(review.get("source_url") or ""),
                    "transformation_log": json.dumps(
                        transformations, ensure_ascii=False, separators=(",", ":")
                    ),
                    "raw_string_name": raw_string_name,
                    "normalized_string_name": normalized_string_name,
                    "canonical_string_name": canonical_name,
                    "string_mapping_status": mapping_status,
                    "brand": str(item.get("brand") or "").strip(),
                    "source_eid": str(item.get("eid") or ""),
                    "language": language_category(normalized_text),
                    "is_code_mixed": language_category(normalized_text)
                    == "mixed_zh_en",
                    # ponytail: heuristic flag only; replace with a validated classifier if
                    # comparison-review recall becomes a measured research requirement.
                    "is_comparison": bool(COMPARISON_PATTERN.search(normalized_text)),
                    "duplicate_group_id": "",
                    "split_group_id": split_group_id,
                    "split": deterministic_split(split_group_id)
                    if split_group_id
                    else "",
                    "rating_label": str(review.get("rating_label") or ""),
                    "likes_count": int(review.get("likes") or 0),
                    "review_date": str(review.get("review_date") or ""),
                }
            )

    id_counts = Counter(
        record["review_id"] for record in records if record["review_id"]
    )
    for record in records:
        if record["review_id"] and id_counts[str(record["review_id"])] > 1:
            record["cleaning_status"] = "invalid"
            reasons = [
                value for value in str(record["exclusion_reason"]).split("|") if value
            ]
            if "duplicate_review_id" not in reasons:
                reasons.append("duplicate_review_id")
            record["exclusion_reason"] = "|".join(reasons)

    raw_groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    normalized_groups: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        raw_key = str(record["raw_text"]).strip()
        normalized_key = str(record["normalized_text"])
        if raw_key:
            raw_groups[raw_key].append(record)
        if normalized_key:
            normalized_groups[normalized_key].append(record)

    group_rows: list[dict[str, object]] = []
    duplicate_ids: set[int] = set()
    for normalized_text, members in sorted(normalized_groups.items()):
        if len(members) < 2:
            continue
        group_id = f"DUP-{review_text_group_id(normalized_text)[:16]}"
        for member in members:
            member["duplicate_group_id"] = group_id
            if member["cleaning_status"] == "included":
                member["cleaning_status"] = "included_duplicate"
            duplicate_ids.add(int(member["source_record_index"]))
        raw_names = sorted({str(member["raw_string_name"]) for member in members})
        group_rows.append(
            {
                "duplicate_group_id": group_id,
                "match_method": "normalized_exact",
                "group_size": len(members),
                "cross_string_group": len(raw_names) > 1,
                "review_ids": "|".join(str(member["review_id"]) for member in members),
                "raw_string_names": "|".join(raw_names),
                "normalized_text": normalized_text,
            }
        )

    frame = pd.DataFrame(records)
    invalid = frame[frame["cleaning_status"] == "invalid"].copy()
    clean = frame[frame["cleaning_status"] != "invalid"].copy()
    duplicates = frame[frame["source_record_index"].isin(duplicate_ids)].copy()
    duplicate_groups = pd.DataFrame(
        group_rows,
        columns=[
            "duplicate_group_id",
            "match_method",
            "group_size",
            "cross_string_group",
            "review_ids",
            "raw_string_names",
            "normalized_text",
        ],
    )
    summary = {
        "raw_reviews": len(frame),
        "clean_reviews": len(clean),
        "invalid_reviews": len(invalid),
        "duplicate_review_id_groups": sum(value > 1 for value in id_counts.values()),
        "exact_raw_text_duplicates": _duplicate_summary(raw_groups),
        "exact_normalized_text_duplicates": _duplicate_summary(normalized_groups),
        "language_distribution": {
            str(key): int(value)
            for key, value in frame["language"].value_counts().items()
        },
        "comparison_reviews": int(frame["is_comparison"].sum()),
        "code_mixed_reviews": int(frame["is_code_mixed"].sum()),
        "transformation_distribution": dict(
            sorted(
                Counter(
                    transformation
                    for value in frame["transformation_log"]
                    for transformation in json.loads(value)
                ).items()
            )
        ),
        "exclusion_reason_distribution": dict(
            sorted(
                Counter(
                    reason
                    for value in invalid["exclusion_reason"]
                    for reason in str(value).split("|")
                    if reason
                ).items()
            )
        ),
    }
    return clean, invalid, duplicates, duplicate_groups, summary


def _historical_leakage(workbench: Path) -> dict[str, int]:
    frame = pd.read_csv(
        workbench / "data/nlp_absa_long_dataset_latest.csv",
        usecols=["sample_id", "review_id", "review_text", "split"],
    )
    return {
        "rows": len(frame),
        "reviews": int(frame["review_id"].nunique()),
        "review_cross_partition_count": int(
            (frame.groupby("review_id")["split"].nunique() > 1).sum()
        ),
        "text_cross_partition_count": int(
            (frame.groupby("review_text", dropna=False)["split"].nunique() > 1).sum()
        ),
        "duplicate_sample_id_count": int(frame["sample_id"].duplicated().sum()),
    }


def _mapping_outputs(
    mappings: pd.DataFrame,
    clean: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, int]]:
    raw_occurrences = clean["raw_string_name"].value_counts().to_dict()
    output = mappings.copy()
    output["occurrence_count"] = (
        output["raw_name"].map(raw_occurrences).fillna(0).astype(int)
    )
    confirmed = output[output["review_status"] == "confirmed"].copy()
    unresolved = output[output["review_status"] != "confirmed"].copy()
    observed_unresolved = clean[clean["string_mapping_status"] != "confirmed"]
    known = set(output["normalized_name"])
    additional_rows = []
    for row in (
        observed_unresolved[["raw_string_name", "normalized_string_name"]]
        .drop_duplicates()
        .itertuples(index=False)
    ):
        if row.normalized_string_name in known:
            continue
        additional_rows.append(
            {
                "raw_name": row.raw_string_name,
                "normalized_name": row.normalized_string_name,
                "canonical_name": "",
                "mapping_method": "unresolved",
                "confidence": 0.0,
                "review_status": "pending",
                "notes": "Needs human review",
                "occurrence_count": int(raw_occurrences.get(row.raw_string_name, 0)),
            }
        )
    if additional_rows:
        unresolved = pd.concat(
            [unresolved, pd.DataFrame(additional_rows)], ignore_index=True
        )
    return (
        confirmed,
        unresolved,
        {
            "confirmed_rows": len(confirmed),
            "pending_or_rejected_rows": len(unresolved),
            "observed_unresolved_reviews": int(len(observed_unresolved)),
        },
    )


def _read_raw_data(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), list):
        raise ValueError("Raw review source must contain a top-level strings array")
    return payload


def _write_csv(path: Path, frame: pd.DataFrame) -> None:
    frame.to_csv(path, index=False, encoding="utf-8-sig")


def _write_markdown(path: Path, report: Mapping[str, object]) -> None:
    cleaning = report["cleaning"]
    leakage = report["leakage"]
    mapping = report["string_name_mapping"]
    silver = report["silver"]
    gold = report["gold"]
    lines = [
        "# StringSense NLP-01 Data Audit",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Raw reviews: {cleaning['raw_reviews']}",
        f"- Clean reviews: {cleaning['clean_reviews']}",
        f"- Invalid reviews: {cleaning['invalid_reviews']}",
        f"- Duplicate review ID groups: {cleaning['duplicate_review_id_groups']}",
        f"- Raw duplicate groups: {cleaning['exact_raw_text_duplicates']['groups']}",
        f"- Normalized duplicate groups: {cleaning['exact_normalized_text_duplicates']['groups']}",
        "",
        "## Language distribution",
        "",
    ]
    lines.extend(
        f"- `{key}`: {value}"
        for key, value in cleaning["language_distribution"].items()
    )
    lines.extend(["", "## Cleaning transformations", ""])
    lines.extend(
        f"- `{key}`: {value}"
        for key, value in cleaning["transformation_distribution"].items()
    )
    lines.extend(["", "## Raw string-name occurrences", ""])
    lines.extend(
        f"- `{key}`: {value}" for key, value in mapping["raw_name_distribution"].items()
    )
    lines.extend(
        [
            "",
            "## String-name mapping",
            "",
            f"- Confirmed mapping rows: {mapping['confirmed_rows']}",
            f"- Pending/rejected mapping rows: {mapping['pending_or_rejected_rows']}",
            f"- Reviews with unresolved observed names: {mapping['observed_unresolved_reviews']}",
            "",
            "## Silver aspect and label distribution",
            "",
        ]
    )
    for aspect, counts in silver["aspect_label_distribution"].items():
        rendered = ", ".join(f"{label}={count}" for label, count in counts.items())
        lines.append(f"- `{aspect}`: {rendered}")
    lines.extend(["", "## Leakage checks", ""])
    for name in ("current_silver", "current_high_confidence"):
        result = leakage[name]
        lines.append(
            f"- `{name}`: review={result['review_cross_partition_count']}, "
            f"text={result['text_cross_partition_count']}, "
            f"group={result['group_cross_partition_count']}"
        )
    historical = leakage["historical_latest_not_for_training"]
    lines.extend(
        [
            "- Historical protected latest is retained for audit only: "
            f"review={historical['review_cross_partition_count']}, "
            f"text={historical['text_cross_partition_count']}",
            "",
            "## Gold status",
            "",
            f"- Pilot sample: {gold['pilot_reviews']} reviews (seed {gold['seed']})",
            f"- Proposed final target: {gold['final_target_reviews']} reviews",
            "- Annotation templates and tools are ready.",
            "- No human Gold labels exist yet.",
            "",
        ]
    )
    with path.open("x", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def run_nlp01(
    run_id: str,
    mapping_path: Path,
    guideline_path: Path,
    sample_size: int = 450,
    seed: int = 42,
    start: Path | None = None,
) -> dict[str, object]:
    workbench = resolve_workbench(start)
    before = fingerprint_inputs(workbench)
    protected_before = fingerprint_protected_assets(workbench)
    stage_dir = create_stage_directory(workbench, run_id, "nlp01")
    root = run_root(workbench, run_id)
    raw_data = _read_raw_data(
        workbench / "data/archive_latest/badminton_strings_data.json"
    )
    mappings = load_string_mappings(mapping_path)
    clean, invalid, duplicates, duplicate_groups, cleaning_summary = (
        build_clean_reviews(raw_data, mappings)
    )
    confirmed, unresolved, mapping_summary = _mapping_outputs(mappings, clean)

    dictionary, rules = load_dictionary_and_rules(workbench)
    silver, high_confidence = build_label_datasets(raw_data, dictionary, rules)
    silver_leakage = leakage_report(silver)
    high_leakage = leakage_report(high_confidence)
    assert_zero_leakage(silver_leakage)
    assert_zero_leakage(high_leakage)
    sample = stratified_sample(clean, silver, sample_size, seed)
    annotator_a = annotation_template(sample, ASPECTS, "A")
    annotator_b = annotation_template(sample, ASPECTS, "B")
    coverage = sampling_coverage(sample, silver)

    audit_report = {
        "schema_version": "stringsense.nlp01-audit.v1",
        "run_id": run_id,
        "created_at": utc_now(),
        "raw_source": {
            "path": "data/archive_latest/badminton_strings_data.json",
            "strings": len(raw_data["strings"]),
            "top_level_fields": sorted(raw_data),
            "string_fields": sorted(
                {key for item in raw_data["strings"] for key in item}
            ),
            "review_fields": sorted(
                {
                    key
                    for item in raw_data["strings"]
                    for review in item.get("reviews", [])
                    for key in review
                }
            ),
        },
        "cleaning": cleaning_summary,
        "string_name_mapping": {
            **mapping_summary,
            "raw_name_distribution": {
                str(key): int(value)
                for key, value in clean["raw_string_name"].value_counts().items()
            },
        },
        "silver": {
            "long_rows": len(silver),
            "high_confidence_rows": len(high_confidence),
            "aspects": sorted(silver["aspect"].unique()),
            "long_label_distribution": {
                str(key): int(value)
                for key, value in silver["label_text"].value_counts().items()
            },
            "high_confidence_label_distribution": {
                str(key): int(value)
                for key, value in high_confidence["label_text"].value_counts().items()
            },
            "aspect_label_distribution": {
                str(aspect): {
                    str(label): int(count)
                    for label, count in group["label_text"].value_counts().items()
                }
                for aspect, group in silver.groupby("aspect", sort=True)
            },
            "provenance": "automatic dictionary weak labels; not human Gold",
        },
        "leakage": {
            "current_silver": silver_leakage,
            "current_high_confidence": high_leakage,
            "historical_latest_not_for_training": _historical_leakage(workbench),
        },
        "gold": {
            "status": "templates_only_no_human_labels",
            "pilot_reviews": sample_size,
            "final_target_reviews": 1200,
            "seed": seed,
            "coverage": coverage,
        },
    }

    paths = {
        "audit_json": stage_dir / "data_audit_report.json",
        "audit_md": stage_dir / "data_audit_report.md",
        "clean": stage_dir / "clean_reviews.csv",
        "invalid": stage_dir / "invalid_reviews.csv",
        "duplicates": stage_dir / "duplicate_reviews.csv",
        "duplicate_groups": stage_dir / "duplicate_review_groups.csv",
        "cleaning_summary": stage_dir / "data_cleaning_summary.json",
        "confirmed_mappings": stage_dir / "confirmed_string_name_mappings.csv",
        "unresolved_mappings": stage_dir / "unresolved_string_names.csv",
        "sampling_plan": stage_dir / "gold_sampling_plan.json",
        "annotation_schema": stage_dir / "annotation_schema.json",
        "annotator_a": stage_dir / "annotator_a_blind.csv",
        "annotator_b": stage_dir / "annotator_b_blind.csv",
        "guideline": stage_dir / "annotation_guideline.md",
    }
    write_json_exclusive(paths["audit_json"], audit_report)
    _write_markdown(paths["audit_md"], audit_report)
    _write_csv(paths["clean"], clean)
    _write_csv(paths["invalid"], invalid)
    _write_csv(paths["duplicates"], duplicates)
    _write_csv(paths["duplicate_groups"], duplicate_groups)
    write_json_exclusive(paths["cleaning_summary"], cleaning_summary)
    _write_csv(paths["confirmed_mappings"], confirmed)
    _write_csv(paths["unresolved_mappings"], unresolved)
    write_json_exclusive(
        paths["sampling_plan"],
        {
            "schema_version": "stringsense.gold-sampling.v1",
            "seed": seed,
            "pilot_reviews": sample_size,
            "final_target_reviews": 1200,
            "per_string_floor": 10,
            "selection": (
                "per-string floor, language floor, then inverse-frequency weighted "
                "sampling"
            ),
            "stratification_inputs": [
                "string",
                "language",
                "silver aspect-label signals",
                "comparison flag",
                "code-mixed flag",
            ],
            "coverage": coverage,
        },
    )
    write_json_exclusive(paths["annotation_schema"], annotation_schema(ASPECTS))
    _write_csv(paths["annotator_a"], annotator_a)
    _write_csv(paths["annotator_b"], annotator_b)
    with paths["guideline"].open("x", encoding="utf-8") as handle:
        handle.write(guideline_path.read_text(encoding="utf-8"))

    after = fingerprint_inputs(workbench)
    assert_inputs_unchanged(before, after)
    protected_after = fingerprint_protected_assets(workbench)
    assert_inputs_unchanged(protected_before, protected_after)
    artifacts = artifact_records(paths.values(), root)
    summary_signature = {
        "cleaning": cleaning_summary,
        "mapping": audit_report["string_name_mapping"],
        "silver": {
            "label_distribution": audit_report["silver"]["long_label_distribution"],
            "aspect_label_distribution": audit_report["silver"][
                "aspect_label_distribution"
            ],
        },
        "leakage": audit_report["leakage"],
        "sampling_coverage": coverage,
    }
    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "run_id": run_id,
        "stage": "nlp01",
        "status": "completed",
        "created_at": utc_now(),
        "inputs": before,
        "protected_assets": protected_before,
        "configuration": {
            "seed": seed,
            "sample_size": sample_size,
            "mapping_path": mapping_path.relative_to(workbench).as_posix(),
            "mapping_sha256": sha256_file(mapping_path),
            "guideline_path": guideline_path.relative_to(workbench).as_posix(),
            "guideline_sha256": sha256_file(guideline_path),
            "duplicate_policy": "flag_and_group_keep_included",
            "aspect_schema": list(ASPECTS),
        },
        "runtime_versions": runtime_versions(("pandas", "numpy", "scikit-learn")),
        "summary_signature": summary_signature,
        "artifacts": artifacts,
        "promotion": {
            "status": "not_promoted",
            "requires_human_approval": True,
            "canonical_artifact_modified": False,
        },
    }
    stage_manifest = stage_dir / "manifest.json"
    write_json_exclusive(stage_manifest, manifest)
    run_manifest = {
        **manifest,
        "stage_manifest": "nlp01/manifest.json",
        "stage_manifest_sha256": sha256_file(stage_manifest),
    }
    run_manifest_path = root / "run_manifest.json"
    write_json_exclusive(run_manifest_path, run_manifest)
    return {
        "run_id": run_id,
        "run_root": str(root),
        "run_manifest_path": str(run_manifest_path),
        "summary_signature": summary_signature,
        "csv_hashes": {
            record["path"]: record["sha256"]
            for record in artifacts
            if str(record["path"]).endswith(".csv")
        },
        "promotion": manifest["promotion"],
    }
