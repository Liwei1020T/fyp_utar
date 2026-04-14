"""remove legacy budget range columns

Revision ID: 20260414_0017
Revises: 20260414_0016
Create Date: 2026-04-14 01:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260414_0017"
down_revision = "20260414_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    columns = {item["name"] for item in inspector.get_columns("profiles")}

    with op.batch_alter_table("profiles") as batch_op:
        if "budget_min" in columns:
            batch_op.drop_column("budget_min")
        if "budget_max" in columns:
            batch_op.drop_column("budget_max")


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the legacy budget range removal migration."
    )
