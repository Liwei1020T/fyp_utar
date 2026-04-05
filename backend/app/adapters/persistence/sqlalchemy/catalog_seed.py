from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


AspectScoreMap = dict[str, float]

TAG_EFFECTS: dict[str, AspectScoreMap] = {
    "弹性好": {"attack": 0.18, "elasticity": 0.22, "sound": 0.12},
    "耐打": {"durability": 0.25, "stability_score": 0.16, "tension_retention": 0.12},
    "控球好": {"control": 0.24, "beginner_fit_score": 0.06},
    "声音清脆": {"sound": 0.26, "attack": 0.08},
    "性价比高": {"value_for_money": 0.28, "beginner_fit_score": 0.08},
    "性价比低": {"value_for_money": -0.24},
    "掉磅快": {"tension_retention": -0.26, "stability_score": -0.10},
    "手感好": {"comfort": 0.20, "control": 0.08},
    "震手": {"comfort": -0.20},
    "粘手": {"string_movement": 0.14, "control": 0.08},
}

ASPECT_KEYS = (
    "attack",
    "comfort",
    "control",
    "durability",
    "elasticity",
    "sound",
    "string_movement",
    "tension_retention",
    "value_for_money",
    "beginner_fit_score",
    "stability_score",
    "all_round_score",
)


def normalize_catalog_name(brand: str, model_name: str) -> str:
    return (
        (f"{brand} {model_name}".strip().lower().replace("-", " ").replace("_", " "))
        .replace("  ", " ")
        .strip()
    )


def load_approved_rows(source_path: Path) -> list[dict[str, Any]]:
    text = source_path.read_text(encoding="utf-8")
    if source_path.suffix.lower() == ".jsonl":
        return [json.loads(line) for line in text.splitlines() if line.strip()]
    if source_path.suffix.lower() == ".json":
        payload = json.loads(text)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return payload["items"]
    raise ValueError(f"Unsupported approved catalog source: {source_path}")


@lru_cache(maxsize=4)
def approved_catalog_defaults(source_path: Path) -> dict[str, dict[str, Any]]:
    rows = load_approved_rows(source_path)
    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        payload = approved_row_to_values(row)
        mapping[payload["normalized_name"]] = payload
    return mapping


def approved_row_to_values(row: dict[str, Any]) -> dict[str, Any]:
    brand = as_string(row.get("brand")) or "Unknown"
    model_name = (
        as_string(row.get("name"))
        or as_string(row.get("model_name"))
        or as_string(row.get("id"))
        or "Unknown"
    )
    normalized_name = normalize_catalog_name(brand, model_name)
    gauge_mm = parse_gauge_mm(as_string(row.get("gauge")))
    tags = parse_tag_list(row.get("top_tags")) + [
        tag["name"] for tag in parse_structured_tags(row.get("tags"))
    ]
    scores = derive_aspect_scores(tags, gauge_mm)

    return {
        "brand": brand,
        "model_name": model_name,
        "normalized_name": normalized_name,
        "price_rm": positive_number(row.get("price")),
        "attack": scores["attack"],
        "comfort": scores["comfort"],
        "control": scores["control"],
        "durability": scores["durability"],
        "elasticity": scores["elasticity"],
        "sound": scores["sound"],
        "string_movement": scores["string_movement"],
        "tension_retention": scores["tension_retention"],
        "value_for_money": scores["value_for_money"],
        "beginner_fit_score": scores["beginner_fit_score"],
        "stability_score": scores["stability_score"],
        "all_round_score": scores["all_round_score"],
        "source_item_id": as_string(row.get("eid")) or as_string(row.get("id")),
        "source_url": as_string(row.get("source_url")),
        "is_active": True,
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

    merged = {**defaults, **overrides}
    merged["brand"] = brand.strip()
    merged["model_name"] = model_name.strip()
    merged["normalized_name"] = normalized_name
    return merged


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
            scores["sound"] = clamp01(scores["sound"] + 0.08)
            scores["durability"] = clamp01(scores["durability"] - 0.08)
            scores["comfort"] = clamp01(scores["comfort"] - 0.05)
        elif gauge_mm >= 0.69:
            scores["durability"] = clamp01(scores["durability"] + 0.20)
            scores["stability_score"] = clamp01(scores["stability_score"] + 0.16)
            scores["tension_retention"] = clamp01(scores["tension_retention"] + 0.08)
            scores["comfort"] = clamp01(scores["comfort"] + 0.08)
            scores["attack"] = clamp01(scores["attack"] - 0.06)
        else:
            scores["control"] = clamp01(scores["control"] + 0.08)
            scores["all_round_score"] = clamp01(scores["all_round_score"] + 0.12)

    scores["beginner_fit_score"] = clamp01(
        (
            scores["comfort"]
            + scores["control"]
            + scores["durability"]
            + scores["value_for_money"]
        )
        / 4
    )
    scores["stability_score"] = clamp01(
        (
            scores["durability"]
            + scores["tension_retention"]
            + (1 - scores["string_movement"])
        )
        / 3
    )
    scores["all_round_score"] = clamp01(
        (
            scores["attack"]
            + scores["comfort"]
            + scores["control"]
            + scores["durability"]
            + scores["elasticity"]
            + scores["sound"]
            + scores["tension_retention"]
            + scores["value_for_money"]
        )
        / 8
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


def as_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return None
