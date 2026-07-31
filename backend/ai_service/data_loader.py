from __future__ import annotations

import csv
import json
import os
import re
from functools import lru_cache
from pathlib import Path

from ai_service.core.config import BACKEND_ROOT
from ai_service.schemas import StringRecord


DEFAULT_MATRIX_PATH = (
    "../ml/nlp-workbench-latest/output/"
    "latest_practical_string_feature_matrix_v8_v6dict.csv"
)
DEFAULT_JSONL_FALLBACK_PATH = (
    BACKEND_ROOT / "data/raw/badminton_strings_recommender.jsonl"
)

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
)

TAG_EFFECTS = {
    "弹性好": {"attack": 0.18, "elasticity": 0.22, "sound": 0.12},
    "耐打": {"durability": 0.25, "tension_retention": 0.12},
    "控球好": {"control": 0.24},
    "声音清脆": {"sound": 0.26, "attack": 0.08},
    "性价比高": {"value_for_money": 0.28},
    "性价比低": {"value_for_money": -0.24},
    "掉磅快": {"tension_retention": -0.26},
    "手感好": {"comfort": 0.2, "control": 0.08},
}


def get_matrix_path() -> Path:
    return _resolve_backend_path(os.getenv("AI_MATRIX_CSV_PATH"), DEFAULT_MATRIX_PATH)


def get_review_signals_path() -> Path | None:
    configured_path = os.getenv("AI_REVIEW_ASPECT_CSV_PATH")
    if not configured_path:
        return None
    return _resolve_backend_path(configured_path, configured_path)


def get_fallback_jsonl_path() -> Path:
    return _resolve_backend_path(
        os.getenv("AI_FALLBACK_JSONL_PATH"),
        str(DEFAULT_JSONL_FALLBACK_PATH),
    )


def _resolve_backend_path(env_value: str | None, default_value: str) -> Path:
    candidate = Path(env_value or default_value)
    if candidate.is_absolute():
        return candidate

    return BACKEND_ROOT / candidate


@lru_cache(maxsize=1)
def load_string_matrix() -> list[StringRecord]:
    matrix_path = get_matrix_path()
    if matrix_path.exists():
        return _load_from_csv(matrix_path)

    fallback_path = get_fallback_jsonl_path()
    if fallback_path.exists():
        return _load_from_jsonl(fallback_path)

    raise FileNotFoundError(
        "No practical string matrix is available. "
        f"Tried {matrix_path} and fallback {fallback_path}."
    )


@lru_cache(maxsize=1)
def load_review_signals() -> list[dict[str, str]]:
    review_path = get_review_signals_path()
    if review_path is None:
        return []
    if not review_path.is_file():
        raise FileNotFoundError(
            f"Configured review aspect signal artifact is missing: {review_path}"
        )

    with review_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def _load_from_csv(matrix_path: Path) -> list[StringRecord]:
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = [row for row in reader]

    records: list[StringRecord] = []
    for row in rows:
        brand = _first_string(
            row,
            "brand",
            "brand_name",
        )
        model_name = _first_string(
            row,
            "model_name",
            "string_name",
            "model",
            "name",
        )
        if not brand or not model_name:
            continue

        values = {
            "brand": brand,
            "model_name": model_name,
            "normalized_name": normalize_catalog_name(brand, model_name),
            "price_rm": _first_number(row, "price_rm", "price", "price_rm_clean"),
            "attack": _aspect_value(row, "attack", "attack_score"),
            "comfort": _aspect_value(row, "comfort", "comfort_score"),
            "control": _aspect_value(row, "control", "control_score"),
            "durability": _aspect_value(row, "durability", "durability_score"),
            "elasticity": _aspect_value(
                row,
                "elasticity",
                "elasticity_score",
                "repulsion_score",
            ),
            "sound": _aspect_value(row, "sound", "sound_score"),
            "string_movement": _aspect_value(
                row,
                "string_movement",
                "string_movement_score",
            ),
            "tension_retention": _aspect_value(
                row,
                "tension_retention",
                "tension_retention_score",
            ),
            "value_for_money": _aspect_value(
                row,
                "value_for_money",
                "value_for_money_score",
                "value_score",
            ),
            "beginner_fit_score": _aspect_value(
                row,
                "beginner_fit_score",
                "beginner_score",
            ),
            "stability_score": _aspect_value(
                row,
                "stability_score",
                "stability",
            ),
            "all_round_score": _aspect_value(
                row,
                "all_round_score",
                "all_round",
            ),
            "source_item_id": _first_string(row, "source_item_id", "id", "eid"),
            "source_url": _first_string(row, "source_url", "url"),
        }
        records.append(StringRecord.model_validate(values))

    return records


def _load_from_jsonl(source_path: Path) -> list[StringRecord]:
    records: list[StringRecord] = []
    with source_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            brand = _as_string(row.get("brand")) or "Unknown"
            model_name = (
                _as_string(row.get("name"))
                or _as_string(row.get("model_name"))
                or _as_string(row.get("id"))
                or "Unknown"
            )
            gauge = _parse_gauge_mm(_as_string(row.get("gauge")))
            tags = _parse_tags(row.get("top_tags")) + [
                tag["name"] for tag in _parse_structured_tags(row.get("tags"))
            ]
            scores = _derive_scores(tags, gauge)
            records.append(
                StringRecord(
                    brand=brand,
                    model_name=model_name,
                    normalized_name=normalize_catalog_name(brand, model_name),
                    price_rm=_positive_number(row.get("price")),
                    attack=scores["attack"],
                    comfort=scores["comfort"],
                    control=scores["control"],
                    durability=scores["durability"],
                    elasticity=scores["elasticity"],
                    sound=scores["sound"],
                    string_movement=scores["string_movement"],
                    tension_retention=scores["tension_retention"],
                    value_for_money=scores["value_for_money"],
                    beginner_fit_score=scores["beginner_fit_score"],
                    stability_score=scores["stability_score"],
                    all_round_score=scores["all_round_score"],
                    source_item_id=_as_string(row.get("eid"))
                    or _as_string(row.get("id")),
                    source_url=_as_string(row.get("source_url")),
                )
            )

    return records


def normalize_catalog_name(brand: str, model_name: str) -> str:
    return " ".join(f"{brand} {model_name}".lower().split())


def normalize_lookup_name(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[\W_]+", " ", value.lower())).strip()


def extract_ascii_words(value: str) -> str | None:
    words = re.findall(r"[a-z0-9]+", value.lower())
    if not words:
        return None
    return " ".join(words)


def _derive_scores(tags: list[str], gauge_mm: float | None) -> dict[str, float]:
    scores = {key: 0.45 for key in ASPECT_KEYS}
    scores["beginner_fit_score"] = 0.45
    scores["stability_score"] = 0.45
    scores["all_round_score"] = 0.45

    for tag in tags:
        effect = TAG_EFFECTS.get(tag)
        if not effect:
            continue
        for aspect, delta in effect.items():
            scores[aspect] = _clamp01(scores[aspect] + delta)

    if gauge_mm is not None:
        if gauge_mm <= 0.65:
            scores["attack"] = _clamp01(scores["attack"] + 0.16)
            scores["elasticity"] = _clamp01(scores["elasticity"] + 0.18)
            scores["sound"] = _clamp01(scores["sound"] + 0.08)
            scores["durability"] = _clamp01(scores["durability"] - 0.08)
        elif gauge_mm >= 0.69:
            scores["durability"] = _clamp01(scores["durability"] + 0.2)
            scores["tension_retention"] = _clamp01(scores["tension_retention"] + 0.08)
            scores["comfort"] = _clamp01(scores["comfort"] + 0.08)
        else:
            scores["control"] = _clamp01(scores["control"] + 0.08)

    scores["beginner_fit_score"] = _clamp01(
        (
            scores["comfort"]
            + scores["control"]
            + scores["durability"]
            + scores["value_for_money"]
        )
        / 4
    )
    scores["stability_score"] = _clamp01(
        (
            scores["durability"]
            + scores["tension_retention"]
            + (1 - scores["string_movement"])
        )
        / 3
    )
    scores["all_round_score"] = _clamp01(
        sum(scores[key] for key in ASPECT_KEYS) / len(ASPECT_KEYS)
    )

    return {key: round(value, 2) for key, value in scores.items()}


def _aspect_value(row: dict[str, str], *keys: str) -> float:
    value = _first_number(row, *keys)
    if value is None:
        return 0.5
    return _normalize_score(value)


def _normalize_score(value: float) -> float:
    if value > 1:
        return _clamp01(value / 5)
    return _clamp01(value)


def _first_number(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        raw = row.get(key)
        if raw is None or raw == "":
            continue
        try:
            return float(raw)
        except ValueError:
            continue
    return None


def _first_string(row: dict[str, str], *keys: str) -> str | None:
    for key in keys:
        raw = row.get(key)
        if raw:
            return raw.strip()
    return None


def _parse_tags(value: object) -> list[str]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    return []


def _parse_structured_tags(value: object) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []

    parsed: list[dict[str, str]] = []
    for item in value:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            parsed.append({"name": item["name"]})
        elif isinstance(item, str):
            parsed.append({"name": item})
    return parsed


def _parse_gauge_mm(value: str | None) -> float | None:
    if not value:
        return None
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)", value)
    if not match:
        return None
    gauge = float(match.group(1))
    return gauge / 100 if gauge > 10 else gauge


def _positive_number(value: object) -> float | None:
    if isinstance(value, (int, float)) and value > 0:
        return float(value)
    if isinstance(value, str) and value.strip():
        try:
            parsed = float(value)
        except ValueError:
            return None
        return parsed if parsed > 0 else None
    return None


def _as_string(value: object) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    return None


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))
