from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.analytics import repository
from src.analytics.schemas import (
    AnalyticsSummaryResponse,
    BreakdownItem,
    BreakdownResponse,
    DeviceBreakdownItem,
    DeviceBreakdownResponse,
    TimeseriesPoint,
    TimeseriesResponse,
)
from src.db.session import get_session
from src.links import service as link_service
from src.models.user import User
from src.shared.rate_limiter import rate_limit


router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/{link_id}/summary", response_model=AnalyticsSummaryResponse)
async def get_summary(
    link_id: int,
    current_user: Annotated[User, Depends(rate_limit("read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AnalyticsSummaryResponse:
    """Return summary analytics for a link."""
    await _authorize_link(session, link_id, current_user)
    total_clicks = await repository.get_total_clicks(session, link_id)
    return AnalyticsSummaryResponse(
        link_id=link_id,
        total_clicks=total_clicks,
        unique_clicks=None,
        unique_clicks_note=(
            "Unique clicks are not tracked yet; current schema stores only "
            "privacy-preserving event hashes and aggregate counts."
        ),
    )


@router.get("/{link_id}/timeseries", response_model=TimeseriesResponse)
async def get_timeseries(
    link_id: int,
    current_user: Annotated[User, Depends(rate_limit("read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
    from_date: Annotated[date, Query(alias="from")],
    to_date: Annotated[date, Query(alias="to")],
    granularity: Literal["day"] = "day",
) -> TimeseriesResponse:
    """Return daily click time series for a link."""
    await _authorize_link(session, link_id, current_user)
    rows = await repository.get_timeseries(session, link_id, from_date, to_date)
    return TimeseriesResponse(
        link_id=link_id,
        granularity=granularity,
        points=[TimeseriesPoint(date=row[0], clicks=row[1]) for row in rows],
    )


@router.get("/{link_id}/geo", response_model=BreakdownResponse)
async def get_geo(
    link_id: int,
    current_user: Annotated[User, Depends(rate_limit("read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BreakdownResponse:
    """Return click breakdown by country."""
    await _authorize_link(session, link_id, current_user)
    rows = await repository.get_geo_breakdown(session, link_id)
    return BreakdownResponse(
        link_id=link_id,
        items=[BreakdownItem(dimension=row[0], clicks=row[1]) for row in rows],
    )


@router.get("/{link_id}/devices", response_model=DeviceBreakdownResponse)
async def get_devices(
    link_id: int,
    current_user: Annotated[User, Depends(rate_limit("read"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DeviceBreakdownResponse:
    """Return click breakdown by device type, browser, and OS."""
    await _authorize_link(session, link_id, current_user)
    rows = await repository.get_device_breakdown(session, link_id)
    return DeviceBreakdownResponse(
        link_id=link_id,
        items=[
            DeviceBreakdownItem(
                device_type=row[0],
                browser=row[1],
                os=row[2],
                clicks=row[3],
            )
            for row in rows
        ],
    )


async def _authorize_link(
    session: AsyncSession,
    link_id: int,
    current_user: User,
) -> None:
    """Raise an HTTP error unless current_user can read the link."""
    try:
        await link_service.get_link(session, link_id, current_user=current_user)
    except link_service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except link_service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
