"""schema drift cleanup

Revision ID: 20260413_0014
Revises: 20260413_0013
Create Date: 2026-04-13 23:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0014"
down_revision = "20260413_0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _rebuild_sqlite_bookings_without_legacy_fk()
    else:
        _drop_named_legacy_booking_fk()

    _backfill_inventory_status_columns()
    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.alter_column(
            "pricing_mode",
            existing_type=sa.String(length=32),
            nullable=False,
        )
        batch_op.alter_column(
            "availability_status",
            existing_type=sa.String(length=32),
            nullable=False,
        )


def _drop_named_legacy_booking_fk() -> None:
    inspector = sa.inspect(op.get_bind())
    legacy_fk_names = [
        fk["name"]
        for fk in inspector.get_foreign_keys("bookings")
        if fk.get("referred_table")
        in {"string_catalog_items", "string_catalog_items_legacy"}
        and fk.get("name")
    ]
    if not legacy_fk_names:
        return

    with op.batch_alter_table("bookings") as batch_op:
        for constraint_name in legacy_fk_names:
            batch_op.drop_constraint(constraint_name, type_="foreignkey")


def _rebuild_sqlite_bookings_without_legacy_fk() -> None:
    op.execute(sa.text("PRAGMA foreign_keys=OFF"))
    op.create_table(
        "_bookings_without_legacy_fk",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("string_id", sa.String(length=120), nullable=False),
        sa.Column("racket_brand", sa.String(length=100), nullable=True),
        sa.Column("racket_model", sa.String(length=100), nullable=True),
        sa.Column("requested_tension", sa.Numeric(4, 1), nullable=True),
        sa.Column("drop_off_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["string_id"],
            ["strings.catalog_id"],
            name="fk_bookings_string_id_strings",
        ),
    )
    op.execute(
        sa.text(
            """
            INSERT INTO _bookings_without_legacy_fk (
                id, user_id, string_id, racket_brand, racket_model,
                requested_tension, drop_off_datetime, notes, status,
                created_at, updated_at
            )
            SELECT
                id, user_id, string_id, racket_brand, racket_model,
                requested_tension, drop_off_datetime, notes, status,
                created_at, updated_at
            FROM bookings
            """
        )
    )
    op.drop_table("bookings")
    op.rename_table("_bookings_without_legacy_fk", "bookings")
    op.create_index("ix_bookings_status", "bookings", ["status"], unique=False)
    op.create_index("ix_bookings_string_id", "bookings", ["string_id"], unique=False)
    op.create_index("ix_bookings_user_id", "bookings", ["user_id"], unique=False)
    op.execute(sa.text("PRAGMA foreign_keys=ON"))


def _backfill_inventory_status_columns() -> None:
    op.execute(
        sa.text(
            """
            UPDATE inventory_items
            SET pricing_mode = CASE
                    WHEN selling_price IS NULL THEN 'price_pending'
                    ELSE 'fixed_price'
                END
            WHERE pricing_mode IS NULL
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE inventory_items
            SET availability_status = CASE
                    WHEN is_active IS FALSE OR available_stock <= 0 THEN 'out_of_stock'
                    WHEN available_stock <= 5 THEN 'low_stock'
                    ELSE 'in_stock'
                END
            WHERE availability_status IS NULL
            """
        )
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the schema drift cleanup migration."
    )
