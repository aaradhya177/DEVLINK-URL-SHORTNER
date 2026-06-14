from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.links import service
from src.links.qr import generate_qr_png, generate_qr_svg
from src.links.schemas import (
    BulkLinkCreateRequest,
    BulkLinkCreateResponse,
    LinkCreate,
    LinkResponse,
    LinkUpdate,
)
from src.models.user import User
from src.shared.cache import get_qr_cache, set_qr_cache
from src.shared.rate_limiter import rate_limit


router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: LinkCreate,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("write"))],
) -> LinkResponse:
    """Create a link for the authenticated user."""
    try:
        link = await service.create_link(session, payload, current_user=current_user)
    except service.InvalidAliasError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.InvalidExpirationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.AliasConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    background_tasks.add_task(service.check_link_safety_by_id, link.id)
    return LinkResponse.model_validate(link)


@router.post("/bulk", response_model=BulkLinkCreateResponse)
async def bulk_create_links(
    payload: BulkLinkCreateRequest,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("bulk"))],
) -> BulkLinkCreateResponse:
    """Create many links with per-item success/error results."""
    try:
        results = await service.bulk_create_links(session, payload, current_user)
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    for result in results:
        if result.link is not None and result.status == "created":
            background_tasks.add_task(service.check_link_safety_by_id, result.link.id)
    return BulkLinkCreateResponse(results=results)


@router.get("", response_model=list[LinkResponse])
async def list_links(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("read"))],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_inactive: bool = False,
) -> list[LinkResponse]:
    """List links with offset pagination for the authenticated user."""
    links = await service.list_links(
        session,
        current_user=current_user,
        limit=limit,
        offset=offset,
        include_inactive=include_inactive,
    )
    return [LinkResponse.model_validate(link) for link in links]


@router.get("/{short_code}/qr")
async def get_link_qr(
    short_code: str,
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
    image_format: Annotated[str, Query(pattern="^(png|svg)$")] = "png",
) -> Response:
    """Return a cached QR code image for a public redirect URL."""
    try:
        link = await service.get_public_link_by_short_code(session, short_code)
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.LinkUnavailableError as exc:
        raise HTTPException(status_code=410, detail=str(exc)) from exc

    cached_image = await get_qr_cache(short_code, image_format)
    if cached_image is not None:
        return _qr_response(cached_image, image_format, "HIT")

    redirect_url = str(request.url_for("redirect_short_code", short_code=short_code))
    image = (
        generate_qr_svg(redirect_url)
        if image_format == "svg"
        else generate_qr_png(redirect_url)
    )
    await set_qr_cache(link.short_code, image_format, image)
    return _qr_response(image, image_format, "MISS")


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("read"))],
) -> LinkResponse:
    """Get one link by ID for the authenticated user."""
    try:
        link = await service.get_link(session, link_id, current_user=current_user)
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)


def _qr_response(image: bytes, image_format: str, cache_status: str) -> Response:
    """Build a QR image response."""
    media_type = "image/svg+xml" if image_format == "svg" else "image/png"
    return Response(
        content=image,
        media_type=media_type,
        headers={
            "Cache-Control": "public, max-age=3600",
            "X-Devlink-Cache": cache_status,
        },
    )


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: int,
    payload: LinkUpdate,
    background_tasks: BackgroundTasks,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("write"))],
) -> LinkResponse:
    """Update one link for the authenticated user."""
    try:
        link = await service.update_link(
            session,
            link_id,
            payload,
            current_user=current_user,
        )
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.InvalidAliasError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.InvalidExpirationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.AliasConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if payload.destination_url is not None:
        background_tasks.add_task(service.check_link_safety_by_id, link.id)
    return LinkResponse.model_validate(link)


@router.delete("/{link_id}", response_model=LinkResponse)
async def delete_link(
    link_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("write"))],
) -> LinkResponse:
    """Soft-delete one link for the authenticated user."""
    try:
        link = await service.soft_delete_link(
            session,
            link_id,
            current_user=current_user,
        )
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)
