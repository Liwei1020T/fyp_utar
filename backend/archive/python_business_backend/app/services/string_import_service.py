from __future__ import annotations

import csv
import json
import re
from collections import Counter
from collections.abc import Iterable
from io import StringIO
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import String
from app.db.models import StringTag
from app.db.session import SessionLocal

TAG_MAP = {
    "弹性好": {"repulsion_score": 1.0, "tag_name_en": "High Repulsion"},
    "耐打": {"durability_score": 1.0, "tag_name_en": "Good Durability"},
    "控球好": {"control_score": 1.0, "tag_name_en": "Good Control"},
    "声音清脆": {"sound_score": 1.0, "tag_name_en": "Crisp Hitting Sound"},
    "性价比高": {"value_score": 1.0, "tag_name_en": "Good Value"},
    "掉磅快": {
        "tension_retention_score": -1.0,
        "tag_name_en": "Weak Tension Retention",
    },
}


def import_strings_jsonl(path: str | Path) -> dict[str, int]:
    normalized_path = Path(path)
    with SessionLocal() as db:
        summary = import_strings_rows(
            db,
            rows=_read_rows_from_path(normalized_path),
        )
        db.commit()
        return summary


def import_strings_rows(db: Session, rows: Iterable[dict[str, Any]]) -> dict[str, int]:
    created_count = 0
    updated_count = 0
    error_count = 0

    for row in rows:
        try:
            string_item, created = _upsert_string(db, row)
            _replace_tags(db, string_item.id, row)
        except ValueError:
            error_count += 1
            continue

        if created:
            created_count += 1
        else:
            updated_count += 1

    return {
        "imported_count": created_count + updated_count,
        "created_count": created_count,
        "updated_count": updated_count,
        "error_count": error_count,
    }


def parse_import_rows(
    *,
    filename: str,
    content: bytes,
) -> list[dict[str, Any]]:
    suffix = Path(filename).suffix.lower()
    text = content.decode("utf-8")
    if suffix == ".jsonl":
        return list(_read_jsonl_rows(text))
    if suffix == ".json":
        return list(_read_json_rows(text))
    if suffix == ".csv":
        return list(_read_csv_rows(text))
    raise ValueError("Unsupported import file format")


def _read_rows_from_path(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")
    if suffix == ".jsonl":
        return list(_read_jsonl_rows(text))
    if suffix == ".json":
        return list(_read_json_rows(text))
    if suffix == ".csv":
        return list(_read_csv_rows(text))
    raise ValueError("Unsupported import file format")


def _read_jsonl_rows(text: str) -> Iterable[dict[str, Any]]:
    for line in text.splitlines():
        if not line.strip():
            continue
        yield json.loads(line)


def _read_json_rows(text: str) -> Iterable[dict[str, Any]]:
    payload = json.loads(text)
    if isinstance(payload, list):
        rows = payload
    elif isinstance(payload, dict) and isinstance(payload.get("items"), list):
        rows = payload["items"]
    else:
        raise ValueError("JSON import must be a list or an object with an items list")

    for row in rows:
        if isinstance(row, dict):
            yield row


def _read_csv_rows(text: str) -> Iterable[dict[str, Any]]:
    reader = csv.DictReader(StringIO(text))
    for row in reader:
        normalized = {key: value for key, value in row.items() if key}
        if not normalized:
            continue
        for field in ("top_tags", "tags"):
            normalized[field] = _parse_list_like(normalized.get(field))
        yield normalized


def _upsert_string(db: Session, row: dict[str, Any]) -> tuple[String, bool]:
    external_id = row.get("id")
    brand = row.get("brand") or "Unknown"
    model_name = row.get("name") or row.get("model_name") or row.get("id") or "Unknown"

    string_item = _find_existing_string(
        db,
        external_id=external_id,
        brand=brand,
        model_name=model_name,
    )
    created = string_item is None
    if string_item is None:
        string_item = String(external_id=external_id)
        db.add(string_item)

    gauge_mm = _parse_gauge_mm(row.get("gauge") or row.get("gauge_raw"))
    scores = _derive_aspect_scores(row)
    recommended_tension_min, recommended_tension_max = _recommended_tension_range(
        gauge_mm
    )

    string_item.external_id = external_id
    string_item.source_item_id = _to_int(row.get("eid") or row.get("source_item_id"))
    string_item.brand = brand
    string_item.brand_en = row.get("brand_en") or row.get("brand")
    string_item.model_name = model_name
    string_item.series = row.get("series")
    string_item.series_en = row.get("series_en") or row.get("series")
    string_item.currency = row.get("currency") or "RM"
    string_item.gauge_raw = row.get("gauge") or row.get("gauge_raw")
    string_item.gauge_mm = gauge_mm
    string_item.material = row.get("material")
    string_item.material_en = row.get("material_en") or row.get("material")
    string_item.color = row.get("color")
    string_item.rating = _to_number(row.get("rating"))
    string_item.rating_5_scale = _to_number(row.get("rating_5_scale"))
    string_item.want_count = _to_int(row.get("want_count"))
    string_item.used_count = _to_int(row.get("used_count"))
    string_item.review_count = _to_int(
        row.get("review_count_total") or row.get("review_count")
    )
    string_item.popularity_signal = _to_int(row.get("popularity_signal"))
    string_item.feature_text = row.get("feature_text")
    string_item.feature_text_en = _feature_text_en(row)
    string_item.source_url = row.get("source_url")
    string_item.repulsion_score = scores.get("repulsion_score")
    string_item.durability_score = scores.get("durability_score")
    string_item.control_score = scores.get("control_score")
    string_item.sound_score = scores.get("sound_score")
    string_item.tension_retention_score = scores.get("tension_retention_score")
    string_item.value_score = scores.get("value_score")
    string_item.availability_status = row.get("availability_status") or "active"
    string_item.recommended_tension_min = (
        _to_int(row.get("recommended_tension_min")) or recommended_tension_min
    )
    string_item.recommended_tension_max = (
        _to_int(row.get("recommended_tension_max")) or recommended_tension_max
    )
    string_item.price = _normalized_price(row.get("price"))
    string_item.description = row.get("description") or row.get("feature_text")
    string_item.is_active = _to_bool(row.get("is_active"), default=True)
    db.flush()
    return string_item, created


def _find_existing_string(
    db: Session,
    *,
    external_id: Any,
    brand: str,
    model_name: str,
) -> String | None:
    if external_id:
        existing = db.execute(
            select(String).where(String.external_id == str(external_id))
        ).scalar_one_or_none()
        if existing is not None:
            return existing

    return db.execute(
        select(String).where(
            String.brand == brand,
            String.model_name == model_name,
        )
    ).scalar_one_or_none()


def _replace_tags(db: Session, string_id: str, row: dict[str, Any]) -> None:
    existing_tags = (
        db.execute(select(StringTag).where(StringTag.string_id == string_id))
        .scalars()
        .all()
    )
    for existing in existing_tags:
        db.delete(existing)

    tag_votes = _collect_tag_votes(row)
    for tag_name, votes in tag_votes.items():
        db.add(
            StringTag(
                string_id=string_id,
                tag_name=tag_name,
                tag_name_en=TAG_MAP.get(tag_name, {}).get("tag_name_en"),
                votes=votes,
            )
        )


def _collect_tag_votes(row: dict[str, Any]) -> Counter[str]:
    counter: Counter[str] = Counter()

    top_tags = row.get("top_tags") or []
    if isinstance(top_tags, list):
        for tag_name in top_tags:
            if isinstance(tag_name, str) and tag_name:
                counter[tag_name] = max(counter[tag_name], 1)

    tags = row.get("tags") or []
    if isinstance(tags, list):
        for item in tags:
            if isinstance(item, dict):
                tag_name = item.get("name")
                votes = _to_int(item.get("votes")) or 1
                if isinstance(tag_name, str) and tag_name:
                    counter[tag_name] = max(counter[tag_name], votes)
            elif isinstance(item, str) and item:
                counter[item] = max(counter[item], 1)

    return counter


def _derive_aspect_scores(row: dict[str, Any]) -> dict[str, float]:
    totals = {
        "repulsion_score": 0.0,
        "durability_score": 0.0,
        "control_score": 0.0,
        "sound_score": 0.0,
        "tension_retention_score": 0.0,
        "value_score": 0.0,
    }
    tag_counter = _collect_tag_votes(row)
    if not tag_counter:
        return totals

    for tag_name, votes in tag_counter.items():
        mapped = TAG_MAP.get(tag_name, {})
        for score_name in totals:
            if score_name in mapped:
                totals[score_name] += mapped[score_name] * votes

    max_votes = max(tag_counter.values())
    normalized: dict[str, float] = {}
    for key, value in totals.items():
        if value > 0:
            normalized[key] = round(min(5.0, 3.0 + (value / max_votes)), 2)
        elif value < 0:
            normalized[key] = round(max(0.0, 3.0 + value), 2)
        else:
            normalized[key] = 0.0
    return normalized


def _parse_gauge_mm(value: object) -> float | None:
    if not isinstance(value, str):
        return None
    if "、" in value or "/" in value:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)", value)
    if match is None:
        return None
    return float(match.group(1))


def _recommended_tension_range(gauge_mm: float | None) -> tuple[int, int]:
    if gauge_mm is None:
        return (20, 28)
    if gauge_mm <= 0.63:
        return (20, 27)
    if gauge_mm <= 0.68:
        return (20, 28)
    return (19, 27)


def _feature_text_en(row: dict[str, Any]) -> str | None:
    tags = _collect_tag_votes(row).keys()
    english_tags = [
        TAG_MAP[tag]["tag_name_en"]
        for tag in tags
        if tag in TAG_MAP and TAG_MAP[tag].get("tag_name_en")
    ]
    if english_tags:
        return ", ".join(dict.fromkeys(english_tags))
    return row.get("feature_text")


def _to_number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalized_price(value: object) -> float | None:
    number = _to_number(value)
    if number in (None, 0, 0.0):
        return None
    return number


def _to_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_bool(value: object, *, default: bool) -> bool:
    if value is None or value == "":
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y"}:
            return True
        if normalized in {"false", "0", "no", "n"}:
            return False
    return default


def _parse_list_like(value: object) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            parsed = json.loads(text)
            return parsed if isinstance(parsed, list) else []
        delimiter = "|" if "|" in text else ","
        return [item.strip() for item in text.split(delimiter) if item.strip()]
    return []
