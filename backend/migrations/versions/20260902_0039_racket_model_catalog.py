"""add the admin-managed racket model catalogue

Revision ID: 20260902_0039
Revises: 20260831_0038
Create Date: 2026-09-02 00:00:00

The existing standard racket identities become editable catalogue rows. Admins
can add or deactivate rows without deleting historical player data.
"""

from __future__ import annotations

from uuid import uuid4

from alembic import op
import sqlalchemy as sa


revision = "20260902_0039"
down_revision = "20260831_0038"
branch_labels = None
depends_on = None

DEFAULT_RACKET_MODELS = (
    ("li ning:axforce 80", "Li-Ning", "Axforce 80"),
    ("victor:auraspeed 90k ii", "Victor", "Auraspeed 90K II"),
    ("victor:thruster ryuga ii", "Victor", "Thruster Ryuga II"),
    ("yonex:arcsaber 11 pro", "Yonex", "Arcsaber 11 Pro"),
    ("yonex:astrox 88d pro", "Yonex", "Astrox 88D Pro"),
    ("yonex:nanoflare 1000 z", "Yonex", "Nanoflare 1000 Z"),
)


def upgrade() -> None:
    bind = op.get_bind()
    if "racket_model_catalog" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "racket_model_catalog",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("model_key", sa.String(length=220), nullable=False),
            sa.Column("brand", sa.String(length=100), nullable=False),
            sa.Column("model", sa.String(length=100), nullable=False),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            ),
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
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("model_key"),
        )
        op.create_index(
            "ix_racket_model_catalog_model_key",
            "racket_model_catalog",
            ["model_key"],
            unique=True,
        )
        op.create_index(
            "ix_racket_model_catalog_is_active",
            "racket_model_catalog",
            ["is_active"],
        )

    existing_keys = {
        row[0]
        for row in bind.execute(sa.text("SELECT model_key FROM racket_model_catalog"))
    }
    for model_key, brand, model in DEFAULT_RACKET_MODELS:
        if model_key in existing_keys:
            continue
        bind.execute(
            sa.text(
                """
                INSERT INTO racket_model_catalog (
                    id, model_key, brand, model, is_active,
                    created_at, updated_at
                ) VALUES (
                    :id, :model_key, :brand, :model, :is_active,
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
                """
            ),
            {
                "id": str(uuid4()),
                "model_key": model_key,
                "brand": brand,
                "model": model,
                "is_active": True,
            },
        )


def downgrade() -> None:
    if "racket_model_catalog" not in sa.inspect(op.get_bind()).get_table_names():
        return
    op.drop_index(
        "ix_racket_model_catalog_is_active",
        table_name="racket_model_catalog",
    )
    op.drop_index(
        "ix_racket_model_catalog_model_key",
        table_name="racket_model_catalog",
    )
    op.drop_table("racket_model_catalog")
