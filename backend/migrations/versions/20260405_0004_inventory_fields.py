"""inventory fields

Revision ID: 20260405_0004
Revises: 20260404_0003
Create Date: 2026-04-05 10:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260405_0004"
down_revision = "20260404_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "string_catalog_items",
        sa.Column(
            "stock_level",
            sa.Integer(),
            nullable=False,
            server_default="8",
        ),
    )
    op.add_column(
        "string_catalog_items",
        sa.Column("admin_note", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("string_catalog_items", "admin_note")
    op.drop_column("string_catalog_items", "stock_level")
