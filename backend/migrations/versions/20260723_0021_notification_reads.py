"""persist notification read event ids

Revision ID: 20260723_0021
Revises: 20260723_0020
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0021"
down_revision = "20260723_0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    if "notification_reads" in sa.inspect(op.get_bind()).get_table_names():
        return

    op.create_table(
        "notification_reads",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("event_id", sa.String(length=160), nullable=False),
        sa.Column(
            "read_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_notification_reads_user_event",
        ),
    )
    op.create_index(
        "ix_notification_reads_user_id",
        "notification_reads",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_reads_user_id",
        table_name="notification_reads",
    )
    op.drop_table("notification_reads")
