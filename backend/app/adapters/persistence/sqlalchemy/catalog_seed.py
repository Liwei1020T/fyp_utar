from __future__ import annotations

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

TAG_EFFECTS: dict[str, AspectScoreMap] = {
    "弹性好": {"attack": 0.18, "elasticity": 0.22, "hitting_sound": 0.12},
    "耐打": {"durability": 0.25, "stability": 0.16, "tension_retention": 0.12},
    "控球好": {"control": 0.24, "beginner_fit": 0.06},
    "声音清脆": {"hitting_sound": 0.26, "attack": 0.08},
    "性价比高": {"value_for_money": 0.28, "beginner_fit": 0.08},
    "性价比低": {"value_for_money": -0.24},
    "掉磅快": {"tension_retention": -0.26, "stability": -0.10},
    "手感好": {"comfort": 0.20, "control": 0.08},
    "震手": {"comfort": -0.20},
    "粘手": {"string_movement": 0.14, "control": 0.08},
}

ASPECT_KEYS = CANONICAL_MATRIX_FEATURE_KEYS


def normalize_catalog_name(brand: str, model_name: str) -> str:
    return " ".join(
        f"{brand} {model_name}".strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
        .split()
    )


def catalog_source_path(source_path: Path) -> Path:
    if source_path.exists() and source_path.suffix.lower() == ".json":
        return source_path
    candidate = source_path.parent.parent / "string_catalog_db_ready.json"
    if candidate.exists():
        return candidate
    return source_path


@lru_cache(maxsize=4)
def load_catalog_source(source_path: Path) -> dict[str, Any]:
    resolved = catalog_source_path(source_path)
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("strings"), list):
        raise ValueError(f"Unsupported normalized catalog source: {resolved}")
    return payload


@lru_cache(maxsize=1)
def load_legacy_rows() -> dict[str, dict[str, Any]]:
    raw_path = (
        Path(__file__).resolve().parents[4]
        / "data/raw/badminton_strings_recommender.jsonl"
    )
    if not raw_path.exists():
        return {}
    mapping: dict[str, dict[str, Any]] = {}
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        original_name = as_string(row.get("name"))
        if original_name:
            mapping[original_name.lower()] = row
    return mapping


@lru_cache(maxsize=4)
def approved_catalog_defaults(source_path: Path) -> dict[str, dict[str, Any]]:
    payload = load_catalog_source(source_path)
    legacy_rows = load_legacy_rows()
    mapping: dict[str, dict[str, Any]] = {}
    for row in payload["strings"]:
        item = approved_row_to_values(
            row,
            legacy_rows.get(str(row.get("original_name", "")).lower()),
        )
        mapping[item["normalized_name"]] = item
    return mapping


def approved_row_to_values(
    row: dict[str, Any],
    legacy_row: dict[str, Any] | None,
) -> dict[str, Any]:
    brand_name = str(row["brand_name"]).strip()
    model_name = str(row["model_name"]).strip()
    normalized_name = normalize_catalog_name(brand_name, model_name)
    scores = derive_scores_from_legacy_row(legacy_row)
    price_rm = positive_number(legacy_row.get("price")) if legacy_row else None
    gauge_mm = number_or_none(row.get("gauge_main_mm"))
    tension_min_lbs, tension_max_lbs = derive_tension_range(gauge_mm)
    gauge_score = normalize_gauge(gauge_mm)
    catalog_id = str(row["catalog_id"]).strip()
    matrix_entries = [
        {
            "feature_key": feature_key,
            "source_layer": "hybrid_derived",
            "raw_value": score,
            "normalized_score": score,
            "confidence": 0.55,
            "evidence_note": "Backfilled from legacy gauge and community tag heuristics.",
            "source_ref": legacy_row.get("source_url")
            if legacy_row
            else row.get("source_dataset_url"),
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
                "confidence": 0.9,
                "evidence_note": "Normalized directly from catalog gauge metadata.",
                "source_ref": row.get("source_dataset_url"),
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
            "short_description": str(row["short_description"]).strip(),
            "full_description": str(row["full_description"]).strip(),
            "official_performance_status": as_string(
                row.get("official_performance_status")
            )
            or "pending_manual_fill",
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
            "community_rating": number_or_none(row.get("community_rating")),
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
            for tag in row.get("community_tags") or []
        ],
        "official_performance": {
            "catalog_id": catalog_id,
            "source_type": None,
            "source_name": None,
            "source_url": None,
            "source_region": None,
            "category": None,
            "feature": None,
            "feel": None,
            "repulsion_power": None,
            "durability": None,
            "hitting_sound": None,
            "shock_absorption": None,
            "control": None,
            "notes": None,
            "status": as_string(row.get("official_performance_status"))
            or "pending_manual_fill",
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
    return {**defaults, "catalog": catalog_values, "normalized_name": normalized_name}


def derive_tension_range(gauge_mm: float | None) -> tuple[int | None, int | None]:
    if gauge_mm is None:
        return None, None
    if gauge_mm <= 0.65:
        return 22, 27
    if gauge_mm >= 0.69:
        return 24, 29
    return 23, 28


def derive_scores_from_legacy_row(legacy_row: dict[str, Any] | None) -> AspectScoreMap:
    if legacy_row is None:
        return {key: 0.5 for key in ASPECT_KEYS}
    gauge_mm = parse_gauge_mm(as_string(legacy_row.get("gauge")))
    tags = parse_tag_list(legacy_row.get("top_tags")) + [
        tag["name"] for tag in parse_structured_tags(legacy_row.get("tags"))
    ]
    return derive_aspect_scores(tags, gauge_mm)


def derive_aspect_scores(tags: list[str], gauge_mm: float | None) -> AspectScoreMap:
    scores: AspectScoreMap = {key: 0.45 for key in ASPECT_KEYS}
    for tag in tags:
        effect = TAG_EFFECTS.get(tag)
        if not effect:
            continue
        for aspect, delta in effect.items():
            scores[aspect] = clamp01(scores[aspect] + delta)

    if gauge_mm is not None:
        if gauge_mm <= 0.65:
            scores["attack"] = clamp01(scores["attack"] + 0.16)
            scores["elasticity"] = clamp01(scores["elasticity"] + 0.18)
            scores["hitting_sound"] = clamp01(scores["hitting_sound"] + 0.08)
            scores["durability"] = clamp01(scores["durability"] - 0.08)
            scores["comfort"] = clamp01(scores["comfort"] - 0.05)
        elif gauge_mm >= 0.69:
            scores["durability"] = clamp01(scores["durability"] + 0.20)
            scores["stability"] = clamp01(scores["stability"] + 0.16)
            scores["tension_retention"] = clamp01(scores["tension_retention"] + 0.08)
            scores["comfort"] = clamp01(scores["comfort"] + 0.08)
            scores["attack"] = clamp01(scores["attack"] - 0.06)
        else:
            scores["control"] = clamp01(scores["control"] + 0.08)
            scores["all_round"] = clamp01(scores["all_round"] + 0.12)

    scores["beginner_fit"] = clamp01(
        (
            scores["comfort"]
            + scores["control"]
            + scores["durability"]
            + scores["value_for_money"]
        )
        / 4
    )
    scores["stability"] = clamp01(
        (
            scores["durability"]
            + scores["tension_retention"]
            + (1 - scores["string_movement"])
        )
        / 3
    )
    scores["all_round"] = clamp01(
        (
            scores["attack"]
            + scores["comfort"]
            + scores["control"]
            + scores["durability"]
            + scores["elasticity"]
            + scores["hitting_sound"]
            + scores["tension_retention"]
            + scores["value_for_money"]
        )
        / 8
    )
    scores["attacking_fit"] = clamp01(
        (
            (scores["attack"] * 0.5)
            + (scores["elasticity"] * 0.3)
            + (scores["hitting_sound"] * 0.2)
        )
    )
    scores["control_fit"] = clamp01(
        (
            (scores["control"] * 0.5)
            + (scores["comfort"] * 0.25)
            + (scores["durability"] * 0.25)
        )
    )
    return {key: round(value, 2) for key, value in scores.items()}


def parse_tag_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def parse_structured_tags(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    tags: list[dict[str, Any]] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            tags.append({"name": item.strip(), "votes": 1})
        elif isinstance(item, dict) and isinstance(item.get("name"), str):
            tags.append(
                {
                    "name": item["name"].strip(),
                    "votes": int(item.get("votes", 1)),
                }
            )
    return tags


def parse_gauge_mm(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
    if not match:
        return None
    gauge = float(match.group(1))
    return gauge / 100 if gauge > 10 else gauge


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
