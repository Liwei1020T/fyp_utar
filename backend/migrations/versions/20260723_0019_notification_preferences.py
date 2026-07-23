"""persist notification preferences

Revision ID: 20260723_0019
Revises: 20260423_0018
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0019"
down_revision = "20260423_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_columns = {item["name"] for item in inspector.get_columns("profiles")}
    if "notification_preferences" in existing_columns:
        return

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(
            sa.Column(
                "notification_preferences",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for notification preferences."
    )
