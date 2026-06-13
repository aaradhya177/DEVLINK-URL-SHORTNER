import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_session
from src.links import service
from src.links.schemas import LinkCreate, LinkResponse, LinkUpdate


router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    payload: LinkCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: uuid.UUID | None = None,
) -> LinkResponse:
    """Create a link for the placeholder user context."""
    try:
        link = await service.create_link(session, payload, owner_id=user_id)
    except service.InvalidAliasError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.InvalidExpirationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.AliasConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)


@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: uuid.UUID | None = None,
) -> LinkResponse:
    """Get one link by ID for the placeholder user context."""
    try:
        link = await service.get_link(session, link_id, owner_id=user_id)
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)


@router.get("", response_model=list[LinkResponse])
async def list_links(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    include_inactive: bool = False,
) -> list[LinkResponse]:
    """List links with offset pagination for the placeholder user context."""
    links = await service.list_links(
        session,
        owner_id=user_id,
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
    user_id: uuid.UUID | None = None,
) -> LinkResponse:
    """Update one link for the placeholder user context."""
    try:
        link = await service.update_link(session, link_id, payload, owner_id=user_id)
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.InvalidAliasError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.InvalidExpirationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except service.AliasConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)


@router.delete("/{link_id}", response_model=LinkResponse)
async def delete_link(
    link_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: uuid.UUID | None = None,
) -> LinkResponse:
    """Soft-delete one link for the placeholder user context."""
    try:
        link = await service.soft_delete_link(session, link_id, owner_id=user_id)
    except service.LinkNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return LinkResponse.model_validate(link)
