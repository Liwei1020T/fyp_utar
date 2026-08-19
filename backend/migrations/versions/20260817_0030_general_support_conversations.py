"""add booking-free player support conversations

Revision ID: 20260817_0030
Revises: 20260813_0029
Create Date: 2026-08-17 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260817_0030"
down_revision = "20260813_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    tables = set(inspector.get_table_names())
    if "support_conversations" not in tables:
        op.create_table(
            "support_conversations",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "player_id",
                sa.String(36),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "state",
                sa.String(20),
                server_default="waiting_admin",
                nullable=False,
            ),
            sa.Column(
                "support_requested_at", sa.DateTime(timezone=True), nullable=False
            ),
            sa.Column("player_last_read_at", sa.DateTime(timezone=True)),
            sa.Column("admin_last_read_at", sa.DateTime(timezone=True)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.CheckConstraint(
                "state IN ('waiting_admin', 'admin_joined', 'resolved', 'closed')",
                name="ck_support_conversations_state",
            ),
            sa.UniqueConstraint("player_id", name="uq_support_conversations_player"),
        )
        op.create_index(
            "ix_support_conversations_player_id",
            "support_conversations",
            ["player_id"],
        )
        op.create_index(
            "ix_support_conversations_state",
            "support_conversations",
            ["state"],
        )

    if "support_conversation_messages" not in tables:
        op.create_table(
            "support_conversation_messages",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column(
                "conversation_id",
                sa.String(36),
                sa.ForeignKey("support_conversations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "author_user_id",
                sa.String(36),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column("author_role", sa.String(20), nullable=False),
            sa.Column("body", sa.Text(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.create_index(
            "ix_support_conversation_messages_conversation_id",
            "support_conversation_messages",
            ["conversation_id"],
        )
        op.create_index(
            "ix_support_conversation_messages_author_user_id",
            "support_conversation_messages",
            ["author_user_id"],
        )
        op.create_index(
            "ix_support_conversation_messages_created_at",
            "support_conversation_messages",
            ["created_at"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_support_conversation_messages_created_at",
        table_name="support_conversation_messages",
    )
    op.drop_index(
        "ix_support_conversation_messages_author_user_id",
        table_name="support_conversation_messages",
    )
    op.drop_index(
        "ix_support_conversation_messages_conversation_id",
        table_name="support_conversation_messages",
    )
    op.drop_table("support_conversation_messages")
    op.drop_index(
        "ix_support_conversations_state",
        table_name="support_conversations",
    )
    op.drop_index(
        "ix_support_conversations_player_id",
        table_name="support_conversations",
    )
    op.drop_table("support_conversations")
