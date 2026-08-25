"""remove the unused store service price setting

Revision ID: 20260825_0034
Revises: 20260825_0033
Create Date: 2026-08-25 00:00:00

The store no longer charges a system service fee. Existing configured values in
the legacy column are intentionally discarded.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260825_0034"
down_revision = "20260825_0033"
branch_labels = None
depends_on = None


def _column_exists(column_name: str) -> bool:
    bind = op.get_bind()
    return any(
        column["name"] == column_name
        for column in sa.inspect(bind).get_columns("store_settings")
    )


def upgrade() -> None:
    if not _column_exists("default_service_price"):
        return
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("store_settings") as batch_op:
            batch_op.drop_column("default_service_price")
        return
    op.drop_column("store_settings", "default_service_price")


def downgrade() -> None:
    if _column_exists("default_service_price"):
        return
    op.add_column(
        "store_settings",
        sa.Column(
            "default_service_price",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0",
        ),
    )
