from __future__ import annotations

import csv
import logging
import re
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from sqlalchemy import select
from sqlalchemy import delete
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
NLP_REVIEW_SOURCE_VERSION = "absa_v8_practical_matrix_v9"


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
    CsvFeatureSpec(
        "stability_score",
        "stability",
        "string_movement_confidence",
        "string_movement_review_raw",
    ),
    CsvFeatureSpec("all_round_score", "all_round"),
    CsvFeatureSpec("attacking_fit_score", "attacking_fit", "attack_confidence"),
    CsvFeatureSpec("control_fit_score", "control_fit", "control_confidence"),
    CsvFeatureSpec("beginner_fit_score", "beginner_fit"),
)

MATRIX_METADATA_COLUMNS = {
    "string_id",
    "string_name",
    "brand",
    "series",
    "gauge_mm",
    "material",
    "price_rm",
    "rating",
    "review_count",
    "budget_tier",
    "attacking_fit_label",
    "control_fit_label",
    "durable_fit_label",
    "crisp_sound_label",
    "source_url",
}

MATRIX_RUNTIME_COLUMNS = MATRIX_METADATA_COLUMNS | {
    column_name
    for spec in CSV_FEATURE_SPECS
    for column_name in (
        spec.column,
        spec.confidence_column,
        spec.evidence_column,
    )
    if column_name
}


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

    rows = _sanitize_matrix_rows(_load_matrix_rows(csv_path))
    lookup = _build_catalog_lookup(db)
    match_counts: Counter[str] = Counter()
    warnings: list[str] = []
    inserted_entries = 0
    updated_entries = 0
    unchanged_entries = 0
    matched_strings = 0
    unmatched_strings = 0
    matched_catalog_ids: set[str] = set()

    for row in rows:
        matched_entry, matched_by, warning = _match_catalog_row(row, lookup)
        if warning:
            warnings.append(warning)
            logger.warning(warning)
        if matched_entry is None:
            unmatched_strings += 1
            continue

        matched_strings += 1
        matched_catalog_ids.add(matched_entry.catalog_id)
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
                "source_version",
                "review_count_snapshot",
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

    allowed_feature_keys = {spec.feature_key for spec in CSV_FEATURE_SPECS}
    if matched_catalog_ids:
        db.execute(
            delete(StringRecommendationMatrix).where(
                StringRecommendationMatrix.source_layer == NLP_REVIEW_SOURCE_LAYER,
                StringRecommendationMatrix.catalog_id.in_(matched_catalog_ids),
                StringRecommendationMatrix.feature_key.not_in(allowed_feature_keys),
            )
        )

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


def _load_matrix_rows(source_path: Path) -> list[dict[str, str]]:
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        return _load_csv_rows(source_path)
    if suffix == ".xlsx":
        return _load_xlsx_rows(source_path)
    raise ValueError(f"Unsupported recommendation matrix source: {source_path}")


def _load_csv_rows(source_path: Path) -> list[dict[str, str]]:
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def _load_xlsx_rows(source_path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(source_path) as workbook:
        shared_strings = _load_shared_strings(workbook)
        sheet_name = _first_sheet_name(workbook)
        sheet_xml = workbook.read(sheet_name)

    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ElementTree.fromstring(sheet_xml)
    rows: list[list[str]] = []
    for row in root.findall(".//main:sheetData/main:row", namespace):
        values: list[str] = []
        current_index = 0
        for cell in row.findall("main:c", namespace):
            cell_ref = cell.attrib.get("r", "")
            cell_index = _column_index(cell_ref)
            while current_index < cell_index:
                values.append("")
                current_index += 1
            values.append(_cell_text(cell, shared_strings, namespace))
            current_index += 1
        rows.append(values)

    if not rows:
        return []
    headers = [value.strip() for value in rows[0]]
    return [
        {
            header: row[index].strip() if index < len(row) else ""
            for index, header in enumerate(headers)
            if header
        }
        for row in rows[1:]
        if any(cell.strip() for cell in row)
    ]


def _sanitize_matrix_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        {key: value for key, value in row.items() if key in MATRIX_RUNTIME_COLUMNS}
        for row in rows
    ]


def _load_shared_strings(workbook: zipfile.ZipFile) -> list[str]:
    try:
        shared_xml = workbook.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    namespace = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    root = ElementTree.fromstring(shared_xml)
    strings: list[str] = []
    for item in root.findall("main:si", namespace):
        parts = [text.text or "" for text in item.findall(".//main:t", namespace)]
        strings.append("".join(parts))
    return strings


def _first_sheet_name(workbook: zipfile.ZipFile) -> str:
    candidates = sorted(
        name
        for name in workbook.namelist()
        if name.startswith("xl/worksheets/sheet") and name.endswith(".xml")
    )
    if not candidates:
        raise ValueError("No worksheets found in recommendation matrix workbook")
    return candidates[0]


def _cell_text(
    cell: ElementTree.Element,
    shared_strings: list[str],
    namespace: dict[str, str],
) -> str:
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(text.text or "" for text in cell.findall(".//main:t", namespace))
    value = cell.find("main:v", namespace)
    raw_value = value.text if value is not None and value.text is not None else ""
    if cell_type == "s" and raw_value:
        index = int(raw_value)
        return shared_strings[index] if index < len(shared_strings) else ""
    return raw_value


def _column_index(cell_ref: str) -> int:
    match = re.match(r"([A-Z]+)", cell_ref)
    if match is None:
        return 0
    index = 0
    for character in match.group(1):
        index = (index * 26) + (ord(character) - ord("A") + 1)
    return index - 1


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
                "source_version": NLP_REVIEW_SOURCE_VERSION,
                "source_generated_at": None,
                "review_count_snapshot": _parse_int(row.get("review_count")),
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


def _parse_int(value: str | None) -> int | None:
    parsed = _parse_float(value)
    if parsed is None:
        return None
    return int(parsed)


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
