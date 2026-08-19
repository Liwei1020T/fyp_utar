"""add player rackets and structured booking feedback

Revision ID: 20260723_0022
Revises: 20260723_0021
Create Date: 2026-07-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260723_0022"
down_revision = "20260723_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    existing_tables = set(inspector.get_table_names())

    if "rackets" not in existing_tables:
        op.create_table(
            "rackets",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("nickname", sa.String(length=80), nullable=False),
            sa.Column("brand", sa.String(length=100), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column("weight_class", sa.String(length=30), nullable=True),
            sa.Column("balance_point", sa.String(length=50), nullable=True),
            sa.Column("grip_size", sa.String(length=30), nullable=True),
            sa.Column("preferred_use", sa.String(length=120), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
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
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_rackets_user_id", "rackets", ["user_id"])

    booking_columns = {item["name"] for item in inspector.get_columns("bookings")}
    if "racket_id" not in booking_columns:
        with op.batch_alter_table("bookings") as batch_op:
            batch_op.add_column(
                sa.Column("racket_id", sa.String(length=36), nullable=True)
            )
            batch_op.create_foreign_key(
                "fk_bookings_racket_id_rackets",
                "rackets",
                ["racket_id"],
                ["id"],
                ondelete="SET NULL",
            )
            batch_op.create_index("ix_bookings_racket_id", ["racket_id"])

    if "booking_feedback" not in existing_tables:
        op.create_table(
            "booking_feedback",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("booking_id", sa.String(length=36), nullable=False),
            sa.Column("user_id", sa.String(length=36), nullable=False),
            sa.Column("rating", sa.Integer(), nullable=False),
            sa.Column("string_feedback", sa.Text(), nullable=True),
            sa.Column("service_feedback", sa.Text(), nullable=True),
            sa.Column("sentiment_tags", sa.JSON(), nullable=False),
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
                "rating >= 1 AND rating <= 5",
                name="ck_booking_feedback_rating",
            ),
            sa.ForeignKeyConstraint(
                ["booking_id"],
                ["bookings.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_booking_feedback_booking_id",
            "booking_feedback",
            ["booking_id"],
            unique=True,
        )
        op.create_index(
            "ix_booking_feedback_user_id",
            "booking_feedback",
            ["user_id"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_booking_feedback_user_id",
        table_name="booking_feedback",
    )
    op.drop_index(
        "ix_booking_feedback_booking_id",
        table_name="booking_feedback",
    )
    op.drop_table("booking_feedback")

    with op.batch_alter_table("bookings") as batch_op:
        batch_op.drop_index("ix_bookings_racket_id")
        batch_op.drop_constraint(
            "fk_bookings_racket_id_rackets",
            type_="foreignkey",
        )
        batch_op.drop_column("racket_id")

    op.drop_index("ix_rackets_user_id", table_name="rackets")
    op.drop_table("rackets")
