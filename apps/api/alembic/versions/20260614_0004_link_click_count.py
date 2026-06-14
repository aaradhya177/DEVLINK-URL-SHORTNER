"""add link click count

Revision ID: 20260614_0004
Revises: 20260614_0003
Create Date: 2026-06-14 01:30:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260614_0004"
down_revision: str | None = "20260614_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "links",
        sa.Column(
            "click_count",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("links", "click_count")
