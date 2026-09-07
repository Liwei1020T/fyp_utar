"""remove unused inventory SKU storage

Revision ID: 20260907_0046
Revises: 20260902_0045
Create Date: 2026-09-07 00:00:00

The current inventory workflow identifies strings by catalog ID and does not
read or write SKU values. Existing SKU values are intentionally discarded
after the live database backup and review gate.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260907_0046"
down_revision = "20260902_0045"
branch_labels = None
depends_on = None


def _column_exists(column_name: str) -> bool:
    return any(
        column["name"] == column_name
        for column in sa.inspect(op.get_bind()).get_columns("inventory_items")
    )


def upgrade() -> None:
    if not _column_exists("sku"):
        return
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("inventory_items") as batch_op:
            batch_op.drop_column("sku")
        return
    op.drop_column("inventory_items", "sku")


def downgrade() -> None:
    if _column_exists("sku"):
        return
    bind = op.get_bind()
    column = sa.Column("sku", sa.String(120), nullable=True)
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("inventory_items") as batch_op:
            batch_op.add_column(column)
            batch_op.create_unique_constraint(
                "inventory_items_sku_key",
                ["sku"],
            )
        return
    op.add_column("inventory_items", column)
    op.create_unique_constraint(
        "inventory_items_sku_key",
        "inventory_items",
        ["sku"],
    )
