from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.link import Link


class LinkAnalyticsDaily(Base):
    __tablename__ = "link_analytics_daily"

    link_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("links.id", ondelete="CASCADE"), primary_key=True
    )
    stat_date: Mapped[date] = mapped_column(Date, primary_key=True)
    country: Mapped[str] = mapped_column(String(2), primary_key=True, default="")
    device_type: Mapped[str] = mapped_column(String(64), primary_key=True, default="")
    browser: Mapped[str] = mapped_column(String(64), primary_key=True, default="")
    os: Mapped[str] = mapped_column(String(64), primary_key=True, default="")
    referer_domain: Mapped[str] = mapped_column(String(255), primary_key=True, default="")
    click_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    link: Mapped["Link"] = relationship(back_populates="daily_analytics")
