import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.workspace import Workspace
from src.models.workspace_member import WorkspaceMember


async def create_workspace(session: AsyncSession, workspace: Workspace) -> Workspace:
    """Persist a workspace."""
    session.add(workspace)
    await session.flush()
    await session.refresh(workspace)
    return workspace


async def get_workspace(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> Workspace | None:
    """Fetch one workspace by ID."""
    return await session.get(Workspace, workspace_id)


async def list_workspaces_for_user(
    session: AsyncSession,
    user_id: uuid.UUID,
) -> Sequence[Workspace]:
    """List workspaces where a user is a member."""
    stmt = (
        select(Workspace)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    result = await session.scalars(stmt)
    return result.all()


async def get_member(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkspaceMember | None:
    """Fetch a workspace member by workspace and user."""
    stmt = select(WorkspaceMember).where(
        WorkspaceMember.workspace_id == workspace_id,
        WorkspaceMember.user_id == user_id,
    )
    return await session.scalar(stmt)


async def list_members(
    session: AsyncSession,
    workspace_id: uuid.UUID,
) -> Sequence[WorkspaceMember]:
    """List all members in a workspace."""
    result = await session.scalars(
        select(WorkspaceMember)
        .where(WorkspaceMember.workspace_id == workspace_id)
        .order_by(WorkspaceMember.created_at.asc())
    )
    return result.all()
