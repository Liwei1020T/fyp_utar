from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.domain.catalog.recommendation_features import (
    CANONICAL_MATRIX_FEATURE_KEYS,
)
from app.domain.catalog.recommendation_features import (
    RECOMMENDATION_FEATURE_DEFINITIONS,
)

AspectScoreMap = dict[str, float]
OFFICIAL_FEEL_BY_CATALOG_ID = {
    "li-ning-n65": 3.0,
    "victor-vbs-68-power": 3.0,
    "yonex-bg65": 3.0,
    "gosen-ryzonic-65": 5.0,
    "kumpoo-js-63": 5.0,
    "li-ning-no1": 5.0,
    "victor-vbs-66-nano": 5.0,
    "yonex-aerobite": 5.0,
    "yonex-bg66-ultimax": 5.0,
    "yonex-exbolt-63": 5.0,
    "yonex-bg80": 8.0,
    "yonex-bg80-power": 8.0,
}


@lru_cache(maxsize=4)
def load_approved_string_cohort(cohort_path: Path) -> dict[str, str]:
    with cohort_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["catalog_id", "canonical_string_name"]:
            raise ValueError(
                "System string cohort must contain catalog_id and canonical_string_name"
            )
        rows = list(reader)
        cohort = {
            str(row["catalog_id"]).strip(): str(row["canonical_string_name"]).strip()
            for row in rows
        }
    if (
        len(rows) != 12
        or len(cohort) != 12
        or len(set(cohort.values())) != 12
        or any(not key or not value for key, value in cohort.items())
    ):
        raise ValueError(
            "System string cohort must contain 12 unique non-blank strings"
        )
    return cohort


def approved_catalog_ids(cohort_path: Path) -> frozenset[str]:
    return frozenset(load_approved_string_cohort(cohort_path))


def normalize_catalog_name(brand: str, model_name: str) -> str:
    return " ".join(
        f"{brand} {model_name}".strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def normalize_catalog_text(value: str) -> str:
    """Keep generated catalog prose free of duplicated sentence punctuation."""
    return re.sub(r"\.{2,}", ".", value.strip())


@lru_cache(maxsize=4)
def load_catalog_source(source_path: Path) -> dict[str, Any]:
    payload = json.loads(source_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), list):
        raise ValueError(f"Unsupported normalized catalog source: {source_path}")
    return payload


@lru_cache(maxsize=4)
def approved_catalog_defaults(source_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_catalog_source(source_path)
    official_performance_by_catalog_id = payload.get("official_performance")
    if not isinstance(official_performance_by_catalog_id, dict):
        official_performance_by_catalog_id = {}
    mapping: dict[str, dict[str, Any]] = {}
    for row in payload["strings"]:
        item = approved_row_to_values(
            row,
            official_performance=official_performance_by_catalog_id.get(
                str(row.get("catalog_id", ""))
            ),
        )
        mapping[item["normalized_name"]] = item
    return mapping


def approved_row_to_values(
    row: dict[str, Any],
    *,
    official_performance: Any = None,
) -> dict[str, Any]:
    brand_name = str(row["brand_name"]).strip()
    model_name = str(row["model_name"]).strip()
    normalized_name = normalize_catalog_name(brand_name, model_name)
    scores = canonical_hybrid_scores(row)
    price_rm = positive_number(row.get("price_rm"))
    gauge_mm = number_or_none(row.get("gauge_main_mm"))
    tension_min_lbs, tension_max_lbs = derive_tension_range(gauge_mm)
    gauge_score = normalize_gauge(gauge_mm)
    catalog_id = str(row["catalog_id"]).strip()
    official_values = (
        official_performance if isinstance(official_performance, dict) else {}
    )
    official_status = (
        as_string(official_values.get("status"))
        or as_string(row.get("official_performance_status"))
        or "pending_manual_fill"
    )
    official_feel = number_or_none(official_values.get("feel"))
    if official_feel is None:
        official_feel = OFFICIAL_FEEL_BY_CATALOG_ID.get(catalog_id)
    matrix_entries = [
        {
            "feature_key": feature_key,
            "source_layer": "hybrid_derived",
            "raw_value": score,
            "normalized_score": score,
            "evidence_note": "Precomputed from canonical catalog feedback and gauge metadata.",
        }
        for feature_key, score in scores.items()
    ]
    if gauge_score is not None:
        matrix_entries.append(
            {
                "feature_key": "gauge_mm",
                "source_layer": "catalog_structured",
                "raw_value": gauge_mm,
                "normalized_score": gauge_score,
                "evidence_note": "Normalized directly from catalog gauge metadata.",
            }
        )

    return {
        "normalized_name": normalized_name,
        "catalog": {
            "catalog_id": catalog_id,
            "brand_code": str(row["brand_code"]).strip(),
            "display_name": str(row["display_name"]).strip(),
            "model_name": model_name,
            "series_key": as_string(row.get("series_key")),
            "series_label": as_string(row.get("series_label")),
            "is_hybrid": bool(row.get("is_hybrid", False)),
            "gauge_main_mm": gauge_mm,
            "gauge_cross_mm": number_or_none(row.get("gauge_cross_mm")),
            "gauge_label": as_string(row.get("gauge_label")),
            "category": None,
            "main_trait": None,
            "tension_min_lbs": tension_min_lbs,
            "tension_max_lbs": tension_max_lbs,
            "material_summary_en": as_string(row.get("material_summary_en")),
            "image_url": None,
            "color_options_en": list(row.get("color_options_en") or []),
            "short_description": normalize_catalog_text(str(row["short_description"])),
            "full_description": normalize_catalog_text(str(row["full_description"])),
            "official_performance_status": official_status,
            "source_dataset_url": as_string(row.get("source_dataset_url")),
            "source_language": as_string(row.get("source_language")) or "en",
            "original_name": as_string(row.get("original_name")),
            "original_brand_label": as_string(row.get("original_brand_label")),
            "original_series": as_string(row.get("original_series")),
            "original_material": as_string(row.get("original_material")),
            "original_color": as_string(row.get("original_color")),
            "is_active": bool(row.get("is_active", True)),
        },
        "metrics": {
            "feedback_rating": number_or_none(row.get("feedback_rating")),
            "want_count": int(row.get("want_count", 0) or 0),
            "used_count": int(row.get("used_count", 0) or 0),
            "review_count": int(row.get("review_count", 0) or 0),
        },
        "tags": [
            {
                "tag_key": str(tag["tag_key"]).strip(),
                "tag_label": str(tag["tag_label"]).strip(),
                "tag_count": int(tag.get("tag_count", 0) or 0),
            }
            for tag in row.get("feedback_tags") or []
        ],
        "official_performance": {
            "catalog_id": catalog_id,
            "source_type": as_string(official_values.get("source_type")),
            "source_name": as_string(official_values.get("source_name")),
            "source_region": as_string(official_values.get("source_region")),
            "category": number_or_none(official_values.get("category")),
            "feature": number_or_none(official_values.get("feature")),
            "feel": official_feel,
            "repulsion_power": number_or_none(official_values.get("repulsion_power")),
            "durability": number_or_none(official_values.get("durability")),
            "hitting_sound": number_or_none(official_values.get("hitting_sound")),
            "shock_absorption": number_or_none(official_values.get("shock_absorption")),
            "control": number_or_none(official_values.get("control")),
            "notes": as_string(official_values.get("notes")),
            "status": official_status,
        },
        "inventory": {
            "catalog_id": catalog_id,
            "sku": build_sku(str(row["brand_code"]), model_name),
            "current_stock": 8,
            "reserved_stock": 0,
            "available_stock": 8,
            "reorder_level": 3,
            "reorder_quantity": 8,
            "cost_price": None,
            "selling_price": price_rm,
            "pricing_mode": "fixed_price" if price_rm is not None else "price_pending",
            "availability_status": "in_stock"
            if bool(row.get("is_active", True))
            else "out_of_stock",
            "is_active": bool(row.get("is_active", True)),
        },
        "matrix_entries": matrix_entries,
    }


def seed_catalog_rows(source_path: Path) -> dict[str, Any]:
    payload = load_catalog_source(source_path)
    defaults = approved_catalog_defaults(source_path)
    return {
        "brands": payload.get("brands", []),
        "items": list(defaults.values()),
        "feature_definitions": RECOMMENDATION_FEATURE_DEFINITIONS,
    }


def merge_with_approved_defaults(
    source_path: Path,
    *,
    brand: str,
    model_name: str,
    overrides: dict[str, Any],
) -> dict[str, Any]:
    normalized_name = normalize_catalog_name(brand, model_name)
    defaults = approved_catalog_defaults(source_path).get(normalized_name)
    if defaults is None:
        raise ValueError("Only approved catalog strings may be created or updated")

    catalog_values = {
        **defaults["catalog"],
        **{
            key: value
            for key, value in overrides.items()
            if key
            in {
                "display_name",
                "series_key",
                "series_label",
                "is_hybrid",
                "gauge_main_mm",
                "gauge_cross_mm",
                "gauge_label",
                "category",
                "main_trait",
                "tension_min_lbs",
                "tension_max_lbs",
                "material_summary_en",
                "image_url",
                "color_options_en",
                "short_description",
                "full_description",
                "source_language",
                "original_name",
                "original_brand_label",
                "original_series",
                "original_material",
                "original_color",
                "is_active",
            }
        },
    }
    catalog_values["display_name"] = (
        str(overrides.get("display_name")).strip()
        if overrides.get("display_name")
        else defaults["catalog"]["display_name"]
    )
    catalog_values["model_name"] = model_name.strip()
    for field_name in ("short_description", "full_description"):
        catalog_values[field_name] = normalize_catalog_text(
            str(catalog_values[field_name])
        )
    return {**defaults, "catalog": catalog_values, "normalized_name": normalized_name}


def derive_tension_range(gauge_mm: float | None) -> tuple[int | None, int | None]:
    if gauge_mm is None:
        return None, None
    if gauge_mm <= 0.65:
        return 22, 27
    if gauge_mm >= 0.69:
        return 24, 29
    return 23, 28


def canonical_hybrid_scores(row: dict[str, Any]) -> AspectScoreMap:
    values = row.get("hybrid_derived_scores")
    if not isinstance(values, dict):
        raise ValueError(
            f"Catalog row {row.get('catalog_id', '<unknown>')} is missing "
            "hybrid_derived_scores"
        )

    scores: AspectScoreMap = {}
    for feature_key in CANONICAL_MATRIX_FEATURE_KEYS:
        score = number_or_none(values.get(feature_key))
        if score is None or not 0 <= score <= 1:
            raise ValueError(
                f"Catalog row {row.get('catalog_id', '<unknown>')} has an invalid "
                f"hybrid score for {feature_key}"
            )
        scores[feature_key] = score
    return scores


def normalize_gauge(value: float | None) -> float | None:
    if value is None:
        return None
    return round(clamp01((value - 0.58) / 0.14), 4)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def positive_number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    if isinstance(value, str) and value.strip():
        parsed = float(value)
        if parsed > 0:
            return parsed
    return None


def number_or_none(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str) and value.strip():
        return float(value)
    return None


def as_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return None


def build_sku(brand_code: str, model_name: str) -> str:
    compact_model = re.sub(r"[^a-zA-Z0-9]+", "-", model_name.strip().lower()).strip("-")
    return f"STR-{brand_code.upper()}-{compact_model.upper()}"
