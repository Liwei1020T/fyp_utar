"""replace budget and game type with recommendation preferences

Revision ID: 20260811_0027
Revises: 20260731_0026
Create Date: 2026-08-11 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "20260811_0027"
down_revision = "20260731_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "profiles",
        sa.Column("preferred_gauge", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "recommendation_score_cache",
        sa.Column("value_for_money_score", sa.Numeric(6, 4), nullable=True),
    )
    op.add_column(
        "recommendation_run_items",
        sa.Column("value_for_money_score", sa.Numeric(6, 4), nullable=True),
    )

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET
                preferred_gauge = COALESCE(preferred_gauge, 'no_preference'),
                preferred_feel = CASE
                    WHEN preferred_feel = 'soft' THEN 'soft'
                    WHEN preferred_feel IN ('crisp', 'hard') THEN 'hard'
                    ELSE 'medium'
                END,
                recent_goal = CASE
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%value%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%price%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%budget%'
                        THEN 'value_for_money'
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%power%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%attack%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%smash%'
                        THEN 'power'
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%control%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%touch%'
                        THEN 'control'
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%durab%'
                        THEN 'durability'
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%comfort%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%soft%'
                        THEN 'comfort'
                    WHEN LOWER(COALESCE(recent_goal, '')) LIKE '%tension%'
                      OR LOWER(COALESCE(recent_goal, '')) LIKE '%retention%'
                        THEN 'tension_retention'
                    ELSE 'balanced'
                END
            """
        )
    )

    feel_by_catalog_id = {
        "li-ning-n65": 3.0,
        "victor-vbs-68-power": 3.0,
        "yonex-bg65": 3.0,
        "gosen-ryzonic-65": 5.0,
        "kumpoo-js-63": 5.0,
        "li-ning-no1": 5.0,
        "victor-vbs-66-nano": 5.0,
        "yonex-aerobite": 5.0,
        "yonex-bg66-ultimax": 5.0,
        "yonex-exbolt-63": 5.0,
        "yonex-bg80": 8.0,
        "yonex-bg80-power": 8.0,
    }
    for catalog_id, feel in feel_by_catalog_id.items():
        op.execute(
            sa.text(
                """
                UPDATE string_official_performance
                SET feel = :feel
                WHERE catalog_id = :catalog_id
                """
            ).bindparams(catalog_id=catalog_id, feel=feel)
        )

    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_column("game_type")
        batch_op.drop_column("budget_tier")


def downgrade() -> None:
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.add_column(sa.Column("budget_tier", sa.String(length=32)))
        batch_op.add_column(sa.Column("game_type", sa.String(length=16)))

    op.drop_column("recommendation_run_items", "value_for_money_score")
    op.drop_column("recommendation_score_cache", "value_for_money_score")
    op.drop_column("profiles", "preferred_gauge")
