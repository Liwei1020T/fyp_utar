"""remove unused official performance source URL

Revision ID: 20260825_0035
Revises: 20260825_0034
Create Date: 2026-08-25 00:00:00

The official performance editor stores curated scores, not external source
links. Catalog and NLP provenance fields remain separate and are unchanged.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260825_0035"
down_revision = "20260825_0034"
branch_labels = None
depends_on = None


def _column_exists(column_name: str) -> bool:
    bind = op.get_bind()
    return any(
        column["name"] == column_name
        for column in sa.inspect(bind).get_columns("string_official_performance")
    )


def upgrade() -> None:
    if not _column_exists("source_url"):
        return
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        with op.batch_alter_table("string_official_performance") as batch_op:
            batch_op.drop_column("source_url")
        return
    op.drop_column("string_official_performance", "source_url")


def downgrade() -> None:
    if _column_exists("source_url"):
        return
    op.add_column(
        "string_official_performance",
        sa.Column("source_url", sa.Text(), nullable=True),
    )
