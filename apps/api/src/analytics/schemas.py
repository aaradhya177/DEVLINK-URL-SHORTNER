from datetime import date

from pydantic import BaseModel


class AnalyticsSummaryResponse(BaseModel):
    """Summary analytics for a single link."""

    link_id: int
    total_clicks: int
    unique_clicks: int | None
    unique_clicks_note: str


class TimeseriesPoint(BaseModel):
    """One time-series analytics point."""

    date: date
    clicks: int


class TimeseriesResponse(BaseModel):
    """Time-series analytics response."""

    link_id: int
    granularity: str
    points: list[TimeseriesPoint]


class BreakdownItem(BaseModel):
    """One grouped analytics breakdown item."""

    dimension: str
    clicks: int


class DeviceBreakdownItem(BaseModel):
    """One device/browser/OS analytics breakdown item."""

    device_type: str
    browser: str
    os: str
    clicks: int


class BreakdownResponse(BaseModel):
    """Generic grouped analytics response."""

    link_id: int
    items: list[BreakdownItem]


class DeviceBreakdownResponse(BaseModel):
    """Device analytics response."""

    link_id: int
    items: list[DeviceBreakdownItem]
