import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.models.workspace import Workspace
from src.models.workspace_member import WorkspaceMember
from src.workspaces import repository
from src.workspaces.schemas import (
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberUpdate,
    WorkspaceUpdate,
)
from src.workspaces.permissions import get_workspace_role


class WorkspaceServiceError(Exception):
    """Base class for workspace service errors."""


class WorkspaceNotFoundError(WorkspaceServiceError):
    """Raised when a workspace does not exist."""


class WorkspaceMemberConflictError(WorkspaceServiceError):
    """Raised when a workspace member already exists."""


class WorkspaceMemberNotFoundError(WorkspaceServiceError):
    """Raised when a workspace member does not exist."""


class WorkspacePermissionError(WorkspaceServiceError):
    """Raised when a workspace action needs stronger permissions."""


async def create_workspace(
    session: AsyncSession,
    payload: WorkspaceCreate,
    current_user: User,
) -> Workspace:
    """Create a workspace and assign the creator as owner."""
    workspace = Workspace(name=payload.name, owner_id=current_user.id)
    await repository.create_workspace(session, workspace)
    session.add(
        WorkspaceMember(
            workspace_id=workspace.id,
            user_id=current_user.id,
            role="owner",
        )
    )
    await session.commit()
    await session.refresh(workspace)
    return workspace


async def get_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> Workspace:
    """Return one workspace or raise when missing."""
    workspace = await repository.get_workspace(session, workspace_id)
    if workspace is None:
        raise WorkspaceNotFoundError("Workspace not found.")
    return workspace


async def list_workspaces(session: AsyncSession, current_user: User) -> list[Workspace]:
    """List workspaces for the current user."""
    return list(await repository.list_workspaces_for_user(session, current_user.id))


async def update_workspace(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    payload: WorkspaceUpdate,
) -> Workspace:
    """Update workspace metadata."""
    workspace = await get_workspace(session, workspace_id)
    workspace.name = payload.name
    workspace.updated_at = datetime.now(UTC)
    await session.commit()
    await session.refresh(workspace)
    return workspace


async def delete_workspace(session: AsyncSession, workspace_id: uuid.UUID) -> None:
    """Delete a workspace and cascading memberships."""
    workspace = await get_workspace(session, workspace_id)
    await session.delete(workspace)
    await session.commit()


async def add_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    payload: WorkspaceMemberCreate,
    current_user: User,
) -> WorkspaceMember:
    """Add a user to a workspace."""
    await get_workspace(session, workspace_id)
    await _ensure_owner_role_change_allowed(
        session,
        workspace_id,
        current_user,
        payload.role,
    )
    member = WorkspaceMember(
        workspace_id=workspace_id,
        user_id=payload.user_id,
        role=payload.role,
    )
    session.add(member)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise WorkspaceMemberConflictError("Workspace member already exists.") from exc

    await session.refresh(member)
    return member


async def list_members(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> list[WorkspaceMember]:
    """List workspace members."""
    await get_workspace(session, workspace_id)
    return list(await repository.list_members(session, workspace_id))


async def update_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: WorkspaceMemberUpdate,
    current_user: User,
) -> WorkspaceMember:
    """Update a workspace member role."""
    member = await repository.get_member(session, workspace_id, user_id)
    if member is None:
        raise WorkspaceMemberNotFoundError("Workspace member not found.")
    await _ensure_owner_role_change_allowed(
        session,
        workspace_id,
        current_user,
        payload.role,
        existing_role=member.role,
    )
    member.role = payload.role
    await session.commit()
    await session.refresh(member)
    return member


async def remove_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User,
) -> None:
    """Remove a workspace member."""
    member = await repository.get_member(session, workspace_id, user_id)
    if member is None:
        raise WorkspaceMemberNotFoundError("Workspace member not found.")
    await _ensure_owner_role_change_allowed(
        session,
        workspace_id,
        current_user,
        target_role="viewer",
        existing_role=member.role,
    )
    await session.delete(member)
    await session.commit()


async def _ensure_owner_role_change_allowed(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    current_user: User,
    target_role: str,
    existing_role: str | None = None,
) -> None:
    """Require an owner for changes that grant or affect owner membership."""
    if target_role != "owner" and existing_role != "owner":
        return

    actor_role = await get_workspace_role(session, workspace_id, current_user.id)
    if actor_role != "owner":
        raise WorkspacePermissionError("Only workspace owners can manage owners.")
