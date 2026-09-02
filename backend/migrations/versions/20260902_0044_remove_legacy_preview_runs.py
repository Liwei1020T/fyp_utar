"""remove recommendation runs created by the old preview bug

Revision ID: 20260902_0044
Revises: 20260902_0043
Create Date: 2026-09-02 00:00:00

Before the preview persistence boundary was fixed, preview requests could be
stored with the request-only ``top_n`` key in ``profile_snapshot``. Current
profile snapshots do not contain that key, so these rows can be removed safely.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260902_0044"
down_revision = "20260902_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        marker = "profile_snapshot::jsonb ? 'top_n'"
    else:
        marker = "json_extract(profile_snapshot, '$.top_n') IS NOT NULL"

    bind.execute(
        sa.text(
            "DELETE FROM recommendation_run_items "
            "WHERE run_id IN ("
            f"SELECT id FROM recommendation_runs WHERE {marker}"
            ")"
        )
    )
    bind.execute(sa.text(f"DELETE FROM recommendation_runs WHERE {marker}"))


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported because removed preview audit "
        "rows cannot be reconstructed safely."
    )
