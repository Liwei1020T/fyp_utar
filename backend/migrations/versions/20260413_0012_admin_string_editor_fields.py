"""admin string editor persisted fields

Revision ID: 20260413_0012
Revises: 20260412_0011
Create Date: 2026-04-13 18:40:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0012"
down_revision = "20260412_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("strings") as batch_op:
        batch_op.add_column(sa.Column("category", sa.String(length=40), nullable=True))
        batch_op.add_column(
            sa.Column("main_trait", sa.String(length=120), nullable=True)
        )
        batch_op.add_column(sa.Column("tension_min_lbs", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("tension_max_lbs", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("image_url", sa.Text(), nullable=True))
        batch_op.create_index("ix_strings_category", ["category"], unique=False)

    with op.batch_alter_table("inventory_items") as batch_op:
        batch_op.add_column(
            sa.Column("pricing_mode", sa.String(length=32), nullable=True)
        )
        batch_op.add_column(
            sa.Column("availability_status", sa.String(length=32), nullable=True)
        )
        batch_op.create_index(
            "ix_inventory_items_availability_status",
            ["availability_status"],
            unique=False,
        )

    op.execute(
        sa.text(
            """
            UPDATE strings
            SET tension_min_lbs = CASE
                    WHEN gauge_main_mm IS NULL THEN NULL
                    WHEN gauge_main_mm <= 0.65 THEN 22
                    WHEN gauge_main_mm >= 0.69 THEN 24
                    ELSE 23
                END,
                tension_max_lbs = CASE
                    WHEN gauge_main_mm IS NULL THEN NULL
                    WHEN gauge_main_mm <= 0.65 THEN 27
                    WHEN gauge_main_mm >= 0.69 THEN 29
                    ELSE 28
                END
            WHERE tension_min_lbs IS NULL OR tension_max_lbs IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE inventory_items
            SET pricing_mode = CASE
                    WHEN selling_price IS NULL THEN 'price_pending'
                    ELSE 'fixed_price'
                END,
                availability_status = CASE
                    WHEN is_active = 0 OR available_stock <= 0 THEN 'out_of_stock'
                    WHEN available_stock <= 5 THEN 'low_stock'
                    ELSE 'in_stock'
                END
            WHERE pricing_mode IS NULL OR availability_status IS NULL
            """
        )
    )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the admin string editor fields migration."
    )
