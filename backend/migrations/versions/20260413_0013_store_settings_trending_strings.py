"""store settings trending strings

Revision ID: 20260413_0013
Revises: 20260413_0012
Create Date: 2026-04-13 23:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260413_0013"
down_revision = "20260413_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("store_settings") as batch_op:
        batch_op.add_column(
            sa.Column(
                "trending_string_ids",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'"),
            )
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the store settings trending strings migration."
    )
