"""remove obsolete feedback tags and legacy catalog tables

Revision ID: 20260902_0040
Revises: 20260902_0039
Create Date: 2026-09-02 00:00:00

The normalized catalog and inventory tables are the only active data boundary.
The old flat catalog tables and removed per-booking sentiment tags are discarded
after fail-closed reference checks. Store settings and normalized catalog data
are never modified by this migration.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0040"
down_revision = "20260902_0039"
branch_labels = None
depends_on = None

REQUIRED_TABLES = {
    "booking_feedback",
    "bookings",
    "inventory_items",
    "store_business_hours",
    "store_settings",
    "strings",
}
LEGACY_TABLES = (
    "string_catalog_items",
    "string_catalog_items_legacy",
    "string_inventory_items",
)


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _assert_required_tables(tables: set[str]) -> None:
    missing = sorted(REQUIRED_TABLES - tables)
    if missing:
        raise RuntimeError(
            "Refusing legacy cleanup because required active tables are missing: "
            + ", ".join(missing)
        )


def _assert_no_foreign_key_references(table_name: str) -> None:
    inspector = sa.inspect(op.get_bind())
    references = []
    for candidate in _table_names():
        if candidate == table_name:
            continue
        for foreign_key in inspector.get_foreign_keys(candidate):
            if foreign_key.get("referred_table") == table_name:
                references.append(
                    f"{candidate}.{foreign_key.get('name') or '<unnamed>'}"
                )
    if references:
        raise RuntimeError(
            f"Refusing to drop {table_name}; foreign keys still reference it: "
            + ", ".join(references)
        )


def _assert_legacy_catalog_rows_are_not_active(table_name: str) -> None:
    bind = op.get_bind()
    unresolved = bind.execute(
        sa.text(
            f"""
            SELECT COUNT(*)
            FROM {table_name} AS legacy
            LEFT JOIN strings AS current_string
              ON current_string.catalog_id = legacy.id
            LEFT JOIN bookings AS booking
              ON booking.string_id = legacy.id
            LEFT JOIN inventory_items AS inventory
              ON inventory.catalog_id = legacy.id
            WHERE current_string.catalog_id IS NULL
              AND (booking.id IS NOT NULL OR inventory.inventory_id IS NOT NULL)
            """
        )
    ).scalar_one()
    if unresolved:
        raise RuntimeError(
            f"Refusing to drop {table_name}; {unresolved} rows are still needed "
            "by bookings or normalized inventory"
        )


def _drop_feedback_tags(tables: set[str]) -> None:
    if "booking_feedback" not in tables:
        return
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("booking_feedback")
    }
    if "sentiment_tags" not in columns:
        return
    if op.get_bind().dialect.name == "sqlite":
        with op.batch_alter_table("booking_feedback") as batch_op:
            batch_op.drop_column("sentiment_tags")
    else:
        op.drop_column("booking_feedback", "sentiment_tags")


def upgrade() -> None:
    bind = op.get_bind()
    tables = _table_names()
    _assert_required_tables(tables)

    unresolved_bookings = bind.execute(
        sa.text(
            """
            SELECT COUNT(*)
            FROM bookings AS booking
            LEFT JOIN strings AS current_string
              ON current_string.catalog_id = booking.string_id
            WHERE current_string.catalog_id IS NULL
            """
        )
    ).scalar_one()
    if unresolved_bookings:
        raise RuntimeError(
            f"Refusing legacy cleanup; {unresolved_bookings} bookings have no "
            "matching normalized string"
        )

    for table_name in LEGACY_TABLES:
        if table_name not in tables:
            continue
        _assert_no_foreign_key_references(table_name)
        if table_name == "string_inventory_items":
            row_count = bind.execute(
                sa.text("SELECT COUNT(*) FROM string_inventory_items")
            ).scalar_one()
            if row_count:
                raise RuntimeError(
                    "Refusing to drop string_inventory_items because it still "
                    f"contains {row_count} rows"
                )
        else:
            _assert_legacy_catalog_rows_are_not_active(table_name)
        op.drop_table(table_name)

    _drop_feedback_tags(tables)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because removed legacy data "
        "cannot be restored from the normalized schema."
    )
