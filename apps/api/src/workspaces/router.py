import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.security import get_current_user
from src.db.session import get_session
from src.models.user import User
from src.workspaces import service
from src.workspaces.dependencies import require_workspace_role
from src.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberResponse,
    WorkspaceMemberUpdate,
    WorkspaceResponse,
    WorkspaceUpdate,
)


router = APIRouter(prefix="/api/v1/workspaces", tags=["workspaces"])


@router.post("", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Create a workspace for the authenticated user."""
    workspace = await service.create_workspace(session, payload, current_user)
    return WorkspaceResponse.model_validate(workspace)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[WorkspaceResponse]:
    """List workspaces for the authenticated user."""
    workspaces = await service.list_workspaces(session, current_user)
    return [WorkspaceResponse.model_validate(workspace) for workspace in workspaces]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: uuid.UUID,
    _: Annotated[User, Depends(require_workspace_role("viewer"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Get one workspace."""
    try:
        workspace = await service.get_workspace(session, workspace_id)
    except service.WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorkspaceResponse.model_validate(workspace)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdate,
    _: Annotated[User, Depends(require_workspace_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceResponse:
    """Update one workspace."""
    try:
        workspace = await service.update_workspace(session, workspace_id, payload)
    except service.WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return WorkspaceResponse.model_validate(workspace)


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace(
    workspace_id: uuid.UUID,
    _: Annotated[User, Depends(require_workspace_role("owner"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Delete one workspace."""
    try:
        await service.delete_workspace(session, workspace_id)
    except service.WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post(
    "/{workspace_id}/members",
    response_model=WorkspaceMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    workspace_id: uuid.UUID,
    payload: WorkspaceMemberCreate,
    current_user: Annotated[User, Depends(require_workspace_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceMemberResponse:
    """Add a member to a workspace."""
    try:
        member = await service.add_member(
            session,
            workspace_id,
            payload,
            current_user,
        )
    except service.WorkspaceNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.WorkspaceMemberConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except service.WorkspacePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return WorkspaceMemberResponse.model_validate(member)


@router.get("/{workspace_id}/members", response_model=list[WorkspaceMemberResponse])
async def list_members(
    workspace_id: uuid.UUID,
    _: Annotated[User, Depends(require_workspace_role("viewer"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[WorkspaceMemberResponse]:
    """List workspace members."""
    members = await service.list_members(session, workspace_id)
    return [WorkspaceMemberResponse.model_validate(member) for member in members]


@router.patch(
    "/{workspace_id}/members/{user_id}",
    response_model=WorkspaceMemberResponse,
)
async def update_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: WorkspaceMemberUpdate,
    current_user: Annotated[User, Depends(require_workspace_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> WorkspaceMemberResponse:
    """Update a workspace member role."""
    try:
        member = await service.update_member(
            session,
            workspace_id,
            user_id,
            payload,
            current_user,
        )
    except service.WorkspaceMemberNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.WorkspacePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return WorkspaceMemberResponse.model_validate(member)


@router.delete(
    "/{workspace_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_member(
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(require_workspace_role("admin"))],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    """Remove a workspace member."""
    try:
        await service.remove_member(session, workspace_id, user_id, current_user)
    except service.WorkspaceMemberNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except service.WorkspacePermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
