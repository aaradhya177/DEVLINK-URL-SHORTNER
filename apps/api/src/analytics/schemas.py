from datetime import date

from pydantic import BaseModel, ConfigDict


class AnalyticsSummaryResponse(BaseModel):
    """Summary analytics for a single link."""

    link_id: int
    total_clicks: int
    unique_clicks: int | None
    unique_clicks_note: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": 742910234935296,
                "total_clicks": 1280,
                "unique_clicks": None,
                "unique_clicks_note": (
                    "Unique clicks are not tracked yet; current schema stores "
                    "only privacy-preserving event hashes and aggregate counts."
                ),
            }
        }
    )


class TimeseriesPoint(BaseModel):
    """One time-series analytics point."""

    date: date
    clicks: int


class TimeseriesResponse(BaseModel):
    """Time-series analytics response."""

    link_id: int
    granularity: str
    points: list[TimeseriesPoint]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": 742910234935296,
                "granularity": "day",
                "points": [
                    {"date": "2026-06-14", "clicks": 42},
                    {"date": "2026-06-15", "clicks": 58},
                ],
            }
        }
    )


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

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": 742910234935296,
                "items": [
                    {"dimension": "US", "clicks": 720},
                    {"dimension": "IN", "clicks": 240},
                ],
            }
        }
    )


class DeviceBreakdownResponse(BaseModel):
    """Device analytics response."""

    link_id: int
    items: list[DeviceBreakdownItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "link_id": 742910234935296,
                "items": [
                    {
                        "device_type": "desktop",
                        "browser": "Chrome",
                        "os": "Windows",
                        "clicks": 620,
                    }
                ],
            }
        }
    )
