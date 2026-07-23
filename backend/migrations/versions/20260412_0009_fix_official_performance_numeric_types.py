"""fix official performance numeric types

Revision ID: 20260412_0009
Revises: 20260412_0008
Create Date: 2026-04-12 18:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260412_0009"
down_revision = "20260412_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    for column_name in ("category", "feature", "feel"):
        op.execute(
            sa.text(
                f"""
                ALTER TABLE string_official_performance
                ALTER COLUMN {column_name}
                TYPE NUMERIC(4, 2)
                USING NULLIF(trim({column_name}::text), '')::numeric
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        return
    for column_name in ("category", "feature", "feel"):
        op.execute(
            sa.text(
                f"""
                ALTER TABLE string_official_performance
                ALTER COLUMN {column_name}
                TYPE VARCHAR(255)
                USING {column_name}::varchar
                """
            )
        )
