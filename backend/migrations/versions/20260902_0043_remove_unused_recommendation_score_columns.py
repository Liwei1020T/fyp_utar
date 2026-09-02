"""remove unused recommendation score compatibility columns

Revision ID: 20260902_0043
Revises: 20260902_0042
Create Date: 2026-09-02 00:00:00

The active recommendation cache and run-item DTOs use the explicit current
score fields. The old duplicate score columns have no current consumers.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0043"
down_revision = "20260902_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table_name, column_names in (
        (
            "recommendation_score_cache",
            (
                "content_score",
                "collaborative_score",
                "rule_score",
                "nlp_score",
                "budget_fit_score",
            ),
        ),
        ("recommendation_run_items", ("budget_fit_score",)),
    ):
        existing = {
            column["name"]
            for column in sa.inspect(op.get_bind()).get_columns(table_name)
        }
        columns_to_drop = [
            column_name for column_name in column_names if column_name in existing
        ]
        if not columns_to_drop:
            continue
        with op.batch_alter_table(table_name) as batch_op:
            for column_name in columns_to_drop:
                batch_op.drop_column(column_name)


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because removed score columns "
        "are no longer part of the active schema."
    )
