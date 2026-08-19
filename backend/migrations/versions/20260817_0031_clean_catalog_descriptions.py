"""clean duplicated punctuation in catalog descriptions

Revision ID: 20260817_0031
Revises: 20260817_0030
Create Date: 2026-08-17 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260817_0031"
down_revision = "20260817_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "strings" not in inspector.get_table_names():
        return
    op.execute(
        sa.text(
            """
            UPDATE strings
            SET short_description = replace(replace(short_description, '...', '.'), '..', '.'),
                full_description = replace(replace(full_description, '...', '.'), '..', '.')
            WHERE short_description LIKE '%..%'
               OR full_description LIKE '%..%'
            """
        )
    )


def downgrade() -> None:
    # Punctuation cleanup is intentionally not reversed; the source normalizer
    # keeps future seeds clean and the previous text is not recoverable safely.
    pass
