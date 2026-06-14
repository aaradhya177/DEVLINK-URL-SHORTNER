from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.links import service
from src.links.schemas import (
    BulkLinkCreateRequest,
    BulkLinkCreateResponse,
    LinkCreate,
    LinkResponse,
    LinkUpdate,
)
from src.models.user import User
from src.shared.rate_limiter import rate_limit


router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: LinkCreate,
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
    return LinkResponse.model_validate(link)


@router.post("/bulk", response_model=BulkLinkCreateResponse)
async def bulk_create_links(
    payload: BulkLinkCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(rate_limit("bulk"))],
) -> BulkLinkCreateResponse:
    """Create many links with per-item success/error results."""
    try:
        results = await service.bulk_create_links(session, payload, current_user)
    except service.LinkPermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return BulkLinkCreateResponse(results=results)


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


@router.patch("/{link_id}", response_model=LinkResponse)
async def update_link(
    link_id: int,
    payload: LinkUpdate,
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
