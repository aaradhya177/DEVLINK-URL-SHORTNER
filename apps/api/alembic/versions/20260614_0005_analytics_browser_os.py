"""add analytics browser os dimensions

Revision ID: 20260614_0005
Revises: 20260614_0004
Create Date: 2026-06-14 02:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260614_0005"
down_revision: str | None = "20260614_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "link_analytics_daily",
        sa.Column("browser", sa.String(length=64), server_default="", nullable=False),
    )
    op.add_column(
        "link_analytics_daily",
        sa.Column("os", sa.String(length=64), server_default="", nullable=False),
    )
    op.drop_constraint(
        "pk_link_analytics_daily",
        "link_analytics_daily",
        type_="primary",
    )
    op.create_primary_key(
        "pk_link_analytics_daily",
        "link_analytics_daily",
        [
            "link_id",
            "stat_date",
            "country",
            "device_type",
            "browser",
            "os",
            "referer_domain",
        ],
    )


def downgrade() -> None:
    op.drop_constraint(
        "pk_link_analytics_daily",
        "link_analytics_daily",
        type_="primary",
    )
    op.create_primary_key(
        "pk_link_analytics_daily",
        "link_analytics_daily",
        ["link_id", "stat_date", "country", "device_type", "referer_domain"],
    )
    op.drop_column("link_analytics_daily", "os")
    op.drop_column("link_analytics_daily", "browser")
