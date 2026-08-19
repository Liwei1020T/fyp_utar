"""add persisted payments and wallet ledger

Revision ID: 20260723_0020
Revises: 20260723_0019
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0020"
down_revision = "20260723_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    existing_tables = set(sa.inspect(op.get_bind()).get_table_names())

    if "payments" not in existing_tables:
        op.create_table(
            "payments",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("booking_id", sa.String(length=36), nullable=True),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("method", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Numeric(10, 2), nullable=False),
            sa.Column("payment_type", sa.String(length=32), nullable=False),
            sa.Column("reference", sa.String(length=80), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
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
            sa.ForeignKeyConstraint(
                ["booking_id"], ["bookings.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_payments_booking_id", "payments", ["booking_id"])
        op.create_index("ix_payments_user_id", "payments", ["user_id"])
        op.create_index("ix_payments_status", "payments", ["status"])
        op.create_index("ix_payments_payment_type", "payments", ["payment_type"])
        op.create_index(
            "ix_payments_reference",
            "payments",
            ["reference"],
            unique=True,
        )

    if "wallet_transactions" not in existing_tables:
        op.create_table(
            "wallet_transactions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("payment_id", sa.String(length=36), nullable=False),
            sa.Column("transaction_type", sa.String(length=32), nullable=False),
            sa.Column("direction", sa.String(length=12), nullable=False),
            sa.Column("amount", sa.Numeric(10, 2), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("method_label", sa.String(length=80), nullable=True),
            sa.Column("related_booking_id", sa.String(length=36), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["payment_id"],
                ["payments.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["related_booking_id"],
                ["bookings.id"],
                ondelete="SET NULL",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_wallet_transactions_user_id", "wallet_transactions", ["user_id"]
        )
        op.create_index(
            "ix_wallet_transactions_payment_id",
            "wallet_transactions",
            ["payment_id"],
            unique=True,
        )


def downgrade() -> None:
    raise NotImplementedError(
        "Downgrade is intentionally unsupported for the commerce ledger."
    )
