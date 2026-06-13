"""initial schema

Revision ID: 20260614_0001
Revises:
Create Date: 2026-06-14 00:00:00.000000

"""
from collections.abc import Sequence
from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260614_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _current_month_partition() -> tuple[str, str, str]:
    now = datetime.now(UTC)
    start = datetime(now.year, now.month, 1, tzinfo=UTC)
    if now.month == 12:
        end = datetime(now.year + 1, 1, 1, tzinfo=UTC)
    else:
        end = datetime(now.year, now.month + 1, 1, tzinfo=UTC)

    name = f"click_events_y{start:%Y}_m{start:%m}"
    return name, start.date().isoformat(), end.date().isoformat()


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name="pk_users"),
    )
    op.create_index(
        "ux_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )

    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
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
            ["owner_id"],
            ["users.id"],
            name="fk_workspaces_owner_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspaces"),
    )
    op.create_index("ix_workspaces_owner_id", "workspaces", ["owner_id"])

    op.create_table(
        "workspace_members",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="viewer"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_workspace_members_user_id_users",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_workspace_members_workspace_id_workspaces",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_workspace_members"),
        sa.UniqueConstraint("workspace_id", "user_id", name="uq_workspace_members_member"),
    )
    op.create_index("ix_workspace_members_user_id", "workspace_members", ["user_id"])
    op.create_index("ix_workspace_members_workspace_id", "workspace_members", ["workspace_id"])

    op.create_table(
        "links",
        sa.Column("id", sa.BigInteger(), autoincrement=False, nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("short_code", sa.String(length=32), nullable=False),
        sa.Column("destination_url", sa.Text(), nullable=False),
        sa.Column("long_url_hash", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
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
            ["owner_id"],
            ["users.id"],
            name="fk_links_owner_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["workspace_id"],
            ["workspaces.id"],
            name="fk_links_workspace_id_workspaces",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_links"),
    )
    # Redirect hot path: one-row lookup by code and code-generation protection.
    op.create_index("ux_links_short_code", "links", ["short_code"], unique=True)
    # Dedup path: hash first supports lookup, workspace_id scopes results.
    op.create_index(
        "ix_links_long_url_hash_workspace_id",
        "links",
        ["long_url_hash", "workspace_id"],
    )
    op.create_index(
        "ix_links_owner_id_created_at",
        "links",
        ["owner_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_links_workspace_id_created_at",
        "links",
        ["workspace_id", sa.text("created_at DESC")],
    )
    op.create_index("ix_links_expires_at", "links", ["expires_at"])
    op.create_index("ix_links_is_active", "links", ["is_active"])
    # Fast rejection for inactive redirects while unique short_code stays authoritative.
    op.create_index(
        "ix_links_active_redirect_lookup",
        "links",
        ["short_code", "expires_at"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "click_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "clicked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("link_id", sa.BigInteger(), nullable=False),
        sa.Column("ip_hash", sa.String(length=128), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=2), nullable=True),
        sa.Column("region", sa.String(length=128), nullable=True),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("device_type", sa.String(length=64), nullable=True),
        sa.Column("browser", sa.String(length=64), nullable=True),
        sa.Column("os", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(
            ["link_id"],
            ["links.id"],
            name="fk_click_events_link_id_links",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", "clicked_at", name="pk_click_events"),
        postgresql_partition_by="RANGE (clicked_at)",
    )
    # Analytics reads filter one link over time; DESC matches newest-first dashboards.
    op.create_index(
        "ix_click_events_link_id_clicked_at",
        "click_events",
        ["link_id", sa.text("clicked_at DESC")],
    )
    # Retention and partition pruning jobs need a direct time index.
    op.create_index("ix_click_events_clicked_at", "click_events", ["clicked_at"])

    partition_name, start_date, end_date = _current_month_partition()
    op.execute(
        sa.text(
            f"""
            CREATE TABLE {partition_name}
            PARTITION OF click_events
            FOR VALUES FROM ('{start_date}') TO ('{end_date}')
            """
        )
    )

    op.create_table(
        "link_analytics_daily",
        sa.Column("link_id", sa.BigInteger(), nullable=False),
        sa.Column("stat_date", sa.Date(), nullable=False),
        sa.Column("country", sa.String(length=2), server_default="", nullable=False),
        sa.Column("device_type", sa.String(length=64), server_default="", nullable=False),
        sa.Column("referer_domain", sa.String(length=255), server_default="", nullable=False),
        sa.Column("click_count", sa.Integer(), server_default="0", nullable=False),
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
            ["link_id"],
            ["links.id"],
            name="fk_link_analytics_daily_link_id_links",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "link_id",
            "stat_date",
            "country",
            "device_type",
            "referer_domain",
            name="pk_link_analytics_daily",
        ),
    )
    op.create_index("ix_link_analytics_daily_stat_date", "link_analytics_daily", ["stat_date"])


def downgrade() -> None:
    op.drop_index("ix_link_analytics_daily_stat_date", table_name="link_analytics_daily")
    op.drop_table("link_analytics_daily")
    op.drop_index("ix_click_events_clicked_at", table_name="click_events")
    op.drop_index("ix_click_events_link_id_clicked_at", table_name="click_events")
    op.drop_table("click_events")
    op.drop_index("ix_links_active_redirect_lookup", table_name="links")
    op.drop_index("ix_links_is_active", table_name="links")
    op.drop_index("ix_links_expires_at", table_name="links")
    op.drop_index("ix_links_workspace_id_created_at", table_name="links")
    op.drop_index("ix_links_owner_id_created_at", table_name="links")
    op.drop_index("ix_links_long_url_hash_workspace_id", table_name="links")
    op.drop_index("ux_links_short_code", table_name="links")
    op.drop_table("links")
    op.drop_index("ix_workspace_members_workspace_id", table_name="workspace_members")
    op.drop_index("ix_workspace_members_user_id", table_name="workspace_members")
    op.drop_table("workspace_members")
    op.drop_index("ix_workspaces_owner_id", table_name="workspaces")
    op.drop_table("workspaces")
    op.drop_index("ux_users_email_lower", table_name="users")
    op.drop_table("users")
