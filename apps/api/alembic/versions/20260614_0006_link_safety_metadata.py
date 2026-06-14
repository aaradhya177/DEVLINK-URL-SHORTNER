"""add link safety metadata

Revision ID: 20260614_0006
Revises: 20260614_0005
Create Date: 2026-06-14 06:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260614_0006"
down_revision: str | None = "20260614_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("links", sa.Column("flagged_reason", sa.Text(), nullable=True))
    op.add_column(
        "links",
        sa.Column("checked_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Maintenance jobs find pending safety checks by checked_at and creation time.
    op.create_index(
        "ix_links_checked_at_created_at",
        "links",
        ["checked_at", "created_at"],
    )
    # Dashboard/status filters and abuse review tools need quick access to flagged rows.
    op.create_index(
        "ix_links_flagged_reason",
        "links",
        ["flagged_reason"],
        postgresql_where=sa.text("flagged_reason IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_links_flagged_reason", table_name="links")
    op.drop_index("ix_links_checked_at_created_at", table_name="links")
    op.drop_column("links", "checked_at")
    op.drop_column("links", "flagged_reason")
