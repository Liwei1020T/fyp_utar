from __future__ import annotations

import csv
import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.adapters.persistence.sqlalchemy.models import RecommendationFeatureDefinition
from app.adapters.persistence.sqlalchemy.models import StringCatalogItem
from app.adapters.persistence.sqlalchemy.models import StringRecommendationMatrix
from app.domain.catalog.entities import RecommendationMatrixImportReport
from app.domain.catalog.recommendation_features import (
    LEGACY_TO_CANONICAL_FEATURE_KEY,
)
from app.domain.catalog.recommendation_features import (
    RECOMMENDATION_FEATURE_DEFINITIONS,
)


logger = logging.getLogger(__name__)

NLP_REVIEW_SOURCE_LAYER = "nlp_review"


@dataclass(frozen=True)
class CsvFeatureSpec:
    column: str
    feature_key: str
    confidence_column: str | None = None
    evidence_column: str | None = None


@dataclass(frozen=True)
class CatalogLookupEntry:
    catalog_id: str
    display_name: str
    model_name: str
    brand_name: str
    brand_code: str
    source_url: str | None
    gauge_mm: float | None
    original_name: str | None
    original_brand_label: str | None


CSV_FEATURE_SPECS = (
    CsvFeatureSpec("attack", "repulsion", "attack_confidence", "attack_review_raw"),
    CsvFeatureSpec("comfort", "comfort", "comfort_confidence", "comfort_review_raw"),
    CsvFeatureSpec("control", "control", "control_confidence", "control_review_raw"),
    CsvFeatureSpec(
        "durability",
        "durability",
        "durability_confidence",
        "durability_review_raw",
    ),
    CsvFeatureSpec(
        "elasticity",
        "elasticity",
        "elasticity_confidence",
        "elasticity_review_raw",
    ),
    CsvFeatureSpec("sound", "sound", "sound_confidence", "sound_review_raw"),
    CsvFeatureSpec(
        "string_movement",
        "string_movement",
        "string_movement_confidence",
        "string_movement_review_raw",
    ),
    CsvFeatureSpec(
        "tension_retention",
        "tension_retention",
        "tension_retention_confidence",
        "tension_retention_review_raw",
    ),
    CsvFeatureSpec(
        "value_for_money",
        "value_for_money",
        "value_for_money_confidence",
        "value_for_money_review_raw",
    ),
    CsvFeatureSpec("stability_score", "stability"),
    CsvFeatureSpec("all_round_score", "all_round"),
    CsvFeatureSpec("attacking_fit_score", "attacking_fit"),
    CsvFeatureSpec("control_fit_score", "control_fit"),
    CsvFeatureSpec("beginner_fit_score", "beginner_fit"),
)


def ensure_recommendation_feature_definitions(db: Session) -> None:
    for feature in RECOMMENDATION_FEATURE_DEFINITIONS:
        db.merge(RecommendationFeatureDefinition(**feature))
    db.flush()


def normalize_legacy_feature_keys(db: Session) -> None:
    legacy_keys = tuple(LEGACY_TO_CANONICAL_FEATURE_KEY)
    legacy_entries = (
        db.execute(
            select(StringRecommendationMatrix).where(
                StringRecommendationMatrix.feature_key.in_(legacy_keys)
            )
        )
        .scalars()
        .all()
    )

    for entry in legacy_entries:
        canonical_key = LEGACY_TO_CANONICAL_FEATURE_KEY[entry.feature_key]
        replacement = db.get(
            StringRecommendationMatrix,
            (entry.catalog_id, canonical_key, entry.source_layer),
        )
        if replacement is None:
            db.add(
                StringRecommendationMatrix(
                    catalog_id=entry.catalog_id,
                    feature_key=canonical_key,
                    source_layer=entry.source_layer,
                    raw_value=entry.raw_value,
                    normalized_score=entry.normalized_score,
                    confidence=entry.confidence,
                    evidence_note=entry.evidence_note,
                    source_ref=entry.source_ref,
                )
            )
        elif (
            replacement.normalized_score is None and entry.normalized_score is not None
        ):
            replacement.raw_value = entry.raw_value
            replacement.normalized_score = entry.normalized_score
            replacement.confidence = entry.confidence
            replacement.evidence_note = entry.evidence_note
            replacement.source_ref = entry.source_ref
        db.delete(entry)

    legacy_definitions = (
        db.execute(
            select(RecommendationFeatureDefinition).where(
                RecommendationFeatureDefinition.feature_key.in_(legacy_keys)
            )
        )
        .scalars()
        .all()
    )
    for definition in legacy_definitions:
        db.delete(definition)

    db.flush()


def import_recommendation_matrix_csv(
    db: Session,
    csv_path: Path,
) -> RecommendationMatrixImportReport:
    ensure_recommendation_feature_definitions(db)
    normalize_legacy_feature_keys(db)

    rows = _load_csv_rows(csv_path)
    lookup = _build_catalog_lookup(db)
    match_counts: Counter[str] = Counter()
    warnings: list[str] = []
    inserted_entries = 0
    updated_entries = 0
    unchanged_entries = 0
    matched_strings = 0
    unmatched_strings = 0

    for row in rows:
        matched_entry, matched_by, warning = _match_catalog_row(row, lookup)
        if warning:
            warnings.append(warning)
            logger.warning(warning)
        if matched_entry is None:
            unmatched_strings += 1
            continue

        matched_strings += 1
        match_counts[matched_by] += 1
        for entry_payload in _build_matrix_entries(row, matched_entry.catalog_id):
            matrix_row = db.get(
                StringRecommendationMatrix,
                (
                    entry_payload["catalog_id"],
                    entry_payload["feature_key"],
                    entry_payload["source_layer"],
                ),
            )
            if matrix_row is None:
                db.add(StringRecommendationMatrix(**entry_payload))
                inserted_entries += 1
                continue

            changed = False
            for field in (
                "raw_value",
                "normalized_score",
                "confidence",
                "evidence_note",
                "source_ref",
            ):
                current_value = getattr(matrix_row, field)
                next_value = entry_payload[field]
                if field in {"raw_value", "normalized_score", "confidence"}:
                    values_match = _same_number(current_value, next_value)
                else:
                    values_match = current_value == next_value
                if not values_match:
                    setattr(matrix_row, field, entry_payload[field])
                    changed = True
            if changed:
                updated_entries += 1
            else:
                unchanged_entries += 1

    db.flush()
    return RecommendationMatrixImportReport(
        csv_path=str(csv_path),
        source_layer=NLP_REVIEW_SOURCE_LAYER,
        total_csv_rows=len(rows),
        matched_strings=matched_strings,
        unmatched_strings=unmatched_strings,
        inserted_entries=inserted_entries,
        updated_entries=updated_entries,
        unchanged_entries=unchanged_entries,
        matched_by=dict(match_counts),
        warnings=warnings,
    )


def _load_csv_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _build_catalog_lookup(db: Session) -> list[CatalogLookupEntry]:
    items = (
        db.execute(
            select(StringCatalogItem).options(selectinload(StringCatalogItem.brand_ref))
        )
        .scalars()
        .all()
    )
    return [
        CatalogLookupEntry(
            catalog_id=item.catalog_id,
            display_name=item.display_name,
            model_name=item.model_name,
            brand_name=item.brand_ref.brand_name,
            brand_code=item.brand_code,
            source_url=item.source_dataset_url,
            gauge_mm=_to_float(item.gauge_main_mm),
            original_name=item.original_name,
            original_brand_label=item.original_brand_label,
        )
        for item in items
    ]


def _match_catalog_row(
    row: dict[str, str],
    lookup: list[CatalogLookupEntry],
) -> tuple[CatalogLookupEntry | None, str, str | None]:
    source_url = _clean_text(row.get("source_url"))
    if source_url:
        exact_source = [entry for entry in lookup if entry.source_url == source_url]
        if len(exact_source) == 1:
            return exact_source[0], "source_url", None
        if len(exact_source) > 1:
            warning = (
                f"Ambiguous source_url match for '{row.get('string_name', '').strip()}': "
                f"{source_url}"
            )
            return None, "ambiguous", warning

    brand_token = _identity_token(row.get("brand"))
    name_token = _identity_token(row.get("string_name"))
    gauge_mm = _parse_float(row.get("gauge_mm"))

    exact_identity = [
        entry
        for entry in lookup
        if _matches_identity(entry, brand_token, name_token, gauge_mm)
    ]
    if len(exact_identity) == 1:
        return exact_identity[0], "brand_name_gauge", None
    if len(exact_identity) > 1:
        warning = (
            f"Ambiguous brand/name/gauge match for '{row.get('string_name', '').strip()}' "
            f"with brand '{row.get('brand', '').strip()}'."
        )
        return None, "ambiguous", warning

    relaxed_identity = [
        entry
        for entry in lookup
        if _matches_identity(entry, brand_token, name_token, None)
    ]
    if len(relaxed_identity) == 1:
        return relaxed_identity[0], "brand_name", None
    if len(relaxed_identity) > 1:
        warning = (
            f"Ambiguous brand/name match for '{row.get('string_name', '').strip()}' "
            f"with brand '{row.get('brand', '').strip()}'."
        )
        return None, "ambiguous", warning

    warning = (
        f"Unmatched recommendation matrix row for '{row.get('string_name', '').strip()}' "
        f"(brand='{row.get('brand', '').strip()}', source_url='{source_url or ''}')."
    )
    return None, "unmatched", warning


def _matches_identity(
    entry: CatalogLookupEntry,
    brand_token: str,
    name_token: str,
    gauge_mm: float | None,
) -> bool:
    brand_candidates = {
        _identity_token(entry.brand_name),
        _identity_token(entry.brand_code),
        _identity_token(entry.original_brand_label),
    }
    name_candidates = {
        _identity_token(entry.display_name),
        _identity_token(entry.model_name),
        _identity_token(entry.original_name),
    }

    if brand_token and brand_token not in brand_candidates:
        return False
    if name_token and name_token not in name_candidates:
        return False
    if gauge_mm is None or entry.gauge_mm is None:
        return True
    return abs(entry.gauge_mm - gauge_mm) <= 0.005


def _build_matrix_entries(
    row: dict[str, str],
    catalog_id: str,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for spec in CSV_FEATURE_SPECS:
        value = _parse_float(row.get(spec.column))
        if value is None:
            continue
        entries.append(
            {
                "catalog_id": catalog_id,
                "feature_key": spec.feature_key,
                "source_layer": NLP_REVIEW_SOURCE_LAYER,
                "raw_value": _round_score(value, digits=4),
                "normalized_score": _round_score(value, digits=4),
                "confidence": _round_score(
                    _parse_float(row.get(spec.confidence_column)),
                    digits=2,
                )
                if spec.confidence_column
                else None,
                "evidence_note": _build_evidence_note(row, spec),
                "source_ref": _clean_text(row.get("source_url")),
            }
        )
    return entries


def _build_evidence_note(row: dict[str, str], spec: CsvFeatureSpec) -> str | None:
    parts: list[str] = []
    review_raw = (
        _clean_text(row.get(spec.evidence_column)) if spec.evidence_column else None
    )
    if review_raw:
        parts.append(f"review_raw={review_raw}")

    if spec.feature_key == "attacking_fit":
        label = _clean_text(row.get("attacking_fit_label"))
        if label:
            parts.append(f"fit_label={label}")
    elif spec.feature_key == "control_fit":
        label = _clean_text(row.get("control_fit_label"))
        if label:
            parts.append(f"fit_label={label}")
    elif spec.feature_key == "stability":
        label = _clean_text(row.get("durable_fit_label"))
        if label:
            parts.append(f"durable_fit_label={label}")
    elif spec.feature_key == "sound":
        label = _clean_text(row.get("crisp_sound_label"))
        if label:
            parts.append(f"crisp_sound_label={label}")

    if spec.feature_key == "beginner_fit":
        review_count = _clean_text(row.get("review_count"))
        budget_tier = _clean_text(row.get("budget_tier"))
        if review_count:
            parts.append(f"review_count={review_count}")
        if budget_tier:
            parts.append(f"budget_tier={budget_tier}")

    if not parts:
        return None
    return "; ".join(parts)


def _identity_token(value: str | None) -> str:
    if not value:
        return ""
    return "".join(char.casefold() for char in value.strip() if char.isalnum())


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _same_number(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is right
    return abs(float(left) - float(right)) <= 1e-9


def _round_score(value: float | None, *, digits: int) -> float | None:
    if value is None:
        return None
    return round(value, digits)
