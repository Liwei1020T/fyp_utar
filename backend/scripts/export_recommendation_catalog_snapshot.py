#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from datetime import UTC
from datetime import datetime
import hashlib
import json
from pathlib import Path
import sys

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.adapters.persistence.sqlalchemy.repositories.sqlalchemy_catalog_repository import (  # noqa: E402
    SqlAlchemyCatalogRepository,
)
from app.adapters.persistence.sqlalchemy.session import SessionLocal  # noqa: E402
from app.adapters.persistence.sqlalchemy.session import engine  # noqa: E402
from app.config.settings import SYSTEM_STRING_COHORT_PATH  # noqa: E402
from app.domain.catalog.entities import StringItem  # noqa: E402


SCHEMA_VERSION = "stringsense.recommendation-catalog-snapshot.v1"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _item_payload(item: StringItem) -> dict[str, object]:
    official = item.official_performance
    inventory = item.inventory
    return {
        "catalog_id": item.id,
        "display_name": item.display_name,
        "is_active": item.is_active,
        "official_performance_status": item.official_performance_status,
        "official_performance": (
            {
                "catalog_id": official.catalog_id,
                "source_type": official.source_type,
                "source_name": official.source_name,
                "source_url": official.source_url,
                "source_region": official.source_region,
                "category": official.category,
                "feature": official.feature,
                "feel": official.feel,
                "repulsion_power": official.repulsion_power,
                "durability": official.durability,
                "hitting_sound": official.hitting_sound,
                "shock_absorption": official.shock_absorption,
                "control": official.control,
                "status": official.status,
                "updated_at": _iso(official.updated_at),
            }
            if official is not None
            else None
        ),
        "inventory": (
            {
                "inventory_id": inventory.inventory_id,
                "current_stock": inventory.current_stock,
                "reserved_stock": inventory.reserved_stock,
                "available_stock": inventory.available_stock,
                "reorder_level": inventory.reorder_level,
                "reorder_quantity": inventory.reorder_quantity,
                "selling_price": inventory.selling_price,
                "pricing_mode": inventory.pricing_mode,
                "availability_status": inventory.availability_status,
                "is_active": inventory.is_active,
                "updated_at": _iso(inventory.updated_at),
                "cost_price_redacted": True,
            }
            if inventory is not None
            else None
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export approved catalog facts for offline recommendation audit"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    with SYSTEM_STRING_COHORT_PATH.open(encoding="utf-8-sig", newline="") as handle:
        approved_ids = {
            row["catalog_id"] for row in csv.DictReader(handle) if row["catalog_id"]
        }
    with SessionLocal() as db:
        if engine.url.get_backend_name() == "postgresql":
            db.execute(text("SET TRANSACTION READ ONLY"))
        items = (
            SqlAlchemyCatalogRepository(
                db,
                approved_catalog_ids=approved_ids,
            )
            .list_strings(
                is_active=None,
                brand=None,
                series=None,
                gauge_min=None,
                gauge_max=None,
                is_hybrid=None,
                search=None,
                sort_by="display_name",
                sort_order="asc",
                limit=None,
                offset=0,
            )
            .items
        )

    found_ids = {item.id for item in items}
    if found_ids != approved_ids:
        raise RuntimeError(
            f"System catalog snapshot mismatch: missing={sorted(approved_ids - found_ids)}, "
            f"unexpected={sorted(found_ids - approved_ids)}"
        )

    catalog = [_item_payload(item) for item in sorted(items, key=lambda row: row.id)]
    coverage = {
        "approved_strings": len(items),
        "active_strings": sum(item.is_active for item in items),
        "official_rows_with_feel": sum(
            item.official_performance is not None
            and item.official_performance.feel is not None
            for item in items
        ),
        "official_rows_with_complete_core_scores": sum(
            item.official_performance is not None
            and item.official_performance.status == "manual_reviewed"
            and all(
                value is not None
                for value in (
                    item.official_performance.repulsion_power,
                    item.official_performance.durability,
                    item.official_performance.hitting_sound,
                    item.official_performance.shock_absorption,
                    item.official_performance.control,
                )
            )
            for item in items
        ),
        "rows_with_selling_price": sum(
            item.inventory is not None and item.inventory.selling_price is not None
            for item in items
        ),
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "source": {
            "database_backend": engine.url.get_backend_name(),
            "transaction_mode": "read_only",
            "approved_cohort_path": str(SYSTEM_STRING_COHORT_PATH),
            "approved_cohort_sha256": _sha256(SYSTEM_STRING_COHORT_PATH),
        },
        "coverage": coverage,
        "catalog": catalog,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"output": str(args.output), **coverage}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
