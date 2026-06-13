import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.click_event import ClickEvent
    from src.models.link_analytics_daily import LinkAnalyticsDaily
    from src.models.user import User
    from src.models.workspace import Workspace


class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="SET NULL")
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    short_code: Mapped[str] = mapped_column(String(32), nullable=False)
    destination_url: Mapped[str] = mapped_column(Text, nullable=False)
    long_url_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    title: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    workspace: Mapped["Workspace | None"] = relationship(back_populates="links")
    owner: Mapped["User | None"] = relationship(back_populates="links")
    click_events: Mapped[list["ClickEvent"]] = relationship(back_populates="link")
    daily_analytics: Mapped[list["LinkAnalyticsDaily"]] = relationship(
        back_populates="link"
    )

    @property
    def is_password_protected(self) -> bool:
        """Return whether this link requires a redirect password."""
        return self.password_hash is not None
